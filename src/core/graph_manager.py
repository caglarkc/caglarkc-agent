from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError
from langgraph.types import Command

from src.core.approval_guard import ApprovalConsumeResult, ApprovalGuard
from src.core.contracts import ApprovalDecision, ApprovalRequest, event_validation_error, validate_event
from src.core.event_bus import EventBus
from src.core.state_transaction import StateTransaction


LOGGER = logging.getLogger(__name__)
ResumeCallback = Callable[[ApprovalDecision], Awaitable[None]]


class GraphManager:
    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        approval_guard: ApprovalGuard | None = None,
        resume_callback: ResumeCallback | None = None,
        reject_callback: ResumeCallback | None = None,
        cancel_callback: ResumeCallback | None = None,
    ) -> None:
        self.event_bus = event_bus or EventBus()
        self.approval_guard = approval_guard or ApprovalGuard()
        self.resume_callback = resume_callback
        self.reject_callback = reject_callback
        self.cancel_callback = cancel_callback
        self.graph = None
        self._thread_configs: dict[str, dict[str, Any]] = {}

    async def start(self) -> None:
        await self.event_bus.subscribe("plan.approval_needed", self.on_plan_approval_needed)
        await self.event_bus.subscribe("plan.approved", self.on_plan_approved)
        await self.event_bus.subscribe("plan.rejected", self.on_plan_rejected)
        await self.event_bus.subscribe("plan.cancelled", self.on_plan_cancelled)

    async def register_approval(self, approval_request: ApprovalRequest) -> None:
        await self.approval_guard.register_approval(approval_request)

    def attach_graph(self, graph: Any) -> None:
        self.graph = graph

    def register_thread(self, thread_id: str, config: dict[str, Any]) -> None:
        self._thread_configs[thread_id] = config

    async def on_plan_approval_needed(self, raw_event: dict[str, Any]) -> None:
        try:
            envelope = validate_event(raw_event)
            approval_request = ApprovalRequest.model_validate(envelope.payload)
        except ValidationError as exc:
            validation_error = event_validation_error(exc)
            LOGGER.warning("Approval request validation failed: %s", validation_error.model_dump())
            return
        await self.register_approval(approval_request)

    async def on_plan_approved(self, raw_event: dict[str, Any]) -> None:
        return await self._handle_decision_event(raw_event, expected_event_type="plan.approved")

    async def on_plan_rejected(self, raw_event: dict[str, Any]) -> None:
        return await self._handle_decision_event(raw_event, expected_event_type="plan.rejected")

    async def on_plan_cancelled(self, raw_event: dict[str, Any]) -> None:
        return await self._handle_decision_event(raw_event, expected_event_type="plan.cancelled")

    async def _handle_decision_event(self, raw_event: dict[str, Any], *, expected_event_type: str) -> ApprovalConsumeResult:
        try:
            envelope = validate_event(raw_event)
        except ValidationError as exc:
            validation_error = event_validation_error(exc)
            LOGGER.warning("Contract validation failed: %s", validation_error.model_dump())
            return ApprovalConsumeResult(outcome="stale", reason=validation_error.message, approval_id="unknown")

        if envelope.event_type != expected_event_type:
            return ApprovalConsumeResult(outcome="stale", reason="event_type_mismatch", approval_id="unknown")
        if not envelope.idempotency_key:
            return ApprovalConsumeResult(outcome="stale", reason="missing_idempotency_key", approval_id="unknown")

        try:
            decision = ApprovalDecision.model_validate(
                {
                    **envelope.payload,
                    "project_id": envelope.project_id,
                    "thread_id": envelope.thread_id,
                    "sprint_id": envelope.sprint_id,
                    "idempotency_key": envelope.idempotency_key,
                }
            )
        except ValidationError as exc:
            validation_error = event_validation_error(exc)
            return ApprovalConsumeResult(outcome="stale", reason=validation_error.message, approval_id="unknown")
        result = await self.approval_guard.consume_decision(decision)

        if result.outcome in {"stale", "no-op"}:
            LOGGER.info("Graph action skipped for %s: %s", decision.approval_id, result.reason)
            return result

        async with StateTransaction(decision.project_id) as transaction:
            state = transaction.state
            approvals = state.setdefault("approvals", {})
            approvals[decision.approval_id] = {
                "decision": decision.decision,
                "idempotency_key": decision.idempotency_key,
                "thread_id": decision.thread_id,
                "sprint_id": decision.sprint_id,
            }
            transaction.state = state

        await self._dispatch_graph_action(decision)
        return result

    async def _dispatch_graph_action(self, decision: ApprovalDecision) -> None:
        if decision.decision == "approved":
            await self._resume_graph(decision)
        elif decision.decision == "rejected":
            await self._stop_graph(decision, terminal_status="rejected", callback=self.reject_callback)
        elif decision.decision == "cancelled":
            await self._stop_graph(decision, terminal_status="cancelled", callback=self.cancel_callback)

    async def _resume_graph(self, decision: ApprovalDecision) -> None:
        if self.resume_callback is not None:
            await self.resume_callback(decision)
        if self.graph is None:
            return
        config = self._thread_configs.get(decision.thread_id)
        if config is None:
            LOGGER.warning("Missing thread config for resume: %s", decision.thread_id)
            return
        snapshot = await self.graph.aget_state(config)
        await self.graph.aupdate_state(
            config,
            {
                "awaiting_approval": False,
                "approval_type": "",
                "active_approval_id": None,
                "messages": [*snapshot.values.get("messages", []), f"approval accepted for {decision.approval_id}"],
            },
            as_node="planner",
        )
        await self.graph.ainvoke(Command(goto="dispatcher"), config=config)

    async def _stop_graph(
        self,
        decision: ApprovalDecision,
        *,
        terminal_status: str,
        callback: ResumeCallback | None,
    ) -> None:
        if callback is not None:
            await callback(decision)
        if self.graph is None:
            return
        config = self._thread_configs.get(decision.thread_id)
        if config is None:
            LOGGER.warning("Missing thread config for stop: %s", decision.thread_id)
            return
        snapshot = await self.graph.aget_state(config)
        await self.graph.aupdate_state(
            config,
            {
                "awaiting_approval": False,
                "approval_type": "",
                "active_approval_id": None,
                "sprint_status": "fail",
                "errors": [*snapshot.values.get("errors", []), {"type": terminal_status, "approval_id": decision.approval_id}],
                "messages": [*snapshot.values.get("messages", []), f"approval {terminal_status} for {decision.approval_id}"],
            },
            as_node="planner",
        )
