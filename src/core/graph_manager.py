from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

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

    async def start(self) -> None:
        await self.event_bus.subscribe("plan.approved", self.on_plan_approved)
        await self.event_bus.subscribe("plan.rejected", self.on_plan_rejected)
        await self.event_bus.subscribe("plan.cancelled", self.on_plan_cancelled)

    async def register_approval(self, approval_request: ApprovalRequest) -> None:
        await self.approval_guard.register_approval(approval_request)

    async def on_plan_approved(self, raw_event: dict[str, Any]) -> None:
        await self._handle_decision_event(raw_event, expected_event_type="plan.approved")

    async def on_plan_rejected(self, raw_event: dict[str, Any]) -> None:
        await self._handle_decision_event(raw_event, expected_event_type="plan.rejected")

    async def on_plan_cancelled(self, raw_event: dict[str, Any]) -> None:
        await self._handle_decision_event(raw_event, expected_event_type="plan.cancelled")

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
        if decision.decision == "approved" and self.resume_callback is not None:
            await self.resume_callback(decision)
        elif decision.decision == "rejected" and self.reject_callback is not None:
            await self.reject_callback(decision)
        elif decision.decision == "cancelled" and self.cancel_callback is not None:
            await self.cancel_callback(decision)
