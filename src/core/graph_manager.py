from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiosqlite
import aiofiles.ospath
from langgraph.types import Command
from pydantic import ValidationError

from src.config.settings import get_settings
from src.core.approval_guard import ApprovalConsumeResult, ApprovalGuard
from src.core.contracts import ApprovalDecision, ApprovalRequest, event_validation_error, new_event, validate_event
from src.core.event_bus import EventBus
from src.core.project_manager import ProjectManager
from src.core.scheduler import FairScheduler, ScheduledTask
from src.core.state_manager import StateManager
from src.core.state_transaction import StateTransaction
from src.graph.graph import build_thread_config, graph_runtime
from src.graph.state import build_initial_state
from src.storage.models import utc_now
from src.storage.repository import Repository


LOGGER = logging.getLogger(__name__)
ResumeCallback = Callable[[ApprovalDecision], Awaitable[None]]
TERMINAL_TASK_STATUSES = {"closed", "rejected", "cancelled"}


class GraphManager:
    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        approval_guard: ApprovalGuard | None = None,
        state_manager: StateManager | None = None,
        repository: Repository | None = None,
        resume_callback: ResumeCallback | None = None,
        reject_callback: ResumeCallback | None = None,
        cancel_callback: ResumeCallback | None = None,
        checkpoint_path: str | Path | None = None,
        graph_runtime_factory: Callable[[str | Path | None], AbstractAsyncContextManager[Any]] = graph_runtime,
        scheduler: FairScheduler | None = None,
    ) -> None:
        settings = get_settings()
        self.event_bus = event_bus or EventBus()
        self.approval_guard = approval_guard or ApprovalGuard()
        self.state_manager = state_manager or StateManager()
        self.repository = repository or Repository()
        self.resume_callback = resume_callback
        self.reject_callback = reject_callback
        self.cancel_callback = cancel_callback
        self.checkpoint_path = Path(checkpoint_path or settings.graph_checkpoint_path)
        self.graph_runtime_factory = graph_runtime_factory
        self.project_manager = ProjectManager(self.repository)
        self.scheduler = scheduler or FairScheduler()
        self.graph = None
        self._runtime_cm: AbstractAsyncContextManager[Any] | None = None
        self._thread_configs: dict[str, dict[str, Any]] = {}
        self._project_threads: dict[str, set[str]] = {}
        self._thread_projects: dict[str, str] = {}
        self._processed_event_ids: set[str] = set()
        self._processed_idempotency_keys: set[str] = set()
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        await self.event_bus.subscribe("plan.approval_needed", self.on_plan_approval_needed)
        await self.event_bus.subscribe("plan.approved", self.on_plan_approved)
        await self.event_bus.subscribe("plan.rejected", self.on_plan_rejected)
        await self.event_bus.subscribe("plan.cancelled", self.on_plan_cancelled)
        await self.event_bus.subscribe("task.received", self.handle_task_received)
        self._started = True

    async def _emit_snapshot_sync(self, project_id: str | None, thread_id: str | None, *, phase: str) -> None:
        await self.event_bus.emit(
            "snapshot.synced",
            new_event(
                "snapshot.synced",
                payload={"project_id": project_id, "phase": phase},
                project_id=project_id,
                thread_id=thread_id,
            ).model_dump(),
        )

    async def _state_for_thread(self, thread_id: str | None) -> dict[str, Any]:
        if not thread_id:
            return {}
        snapshot = await self.state_manager.snapshot()
        for state in snapshot.values():
            if not isinstance(state, dict):
                continue
            if state.get("planning_thread_id") == thread_id or state.get("current_thread_id") == thread_id:
                return state
        return {}

    async def handle_task_received(self, raw_event: dict[str, Any]) -> None:
        """Runs planner for a new user task (CLI/Telegram) and persists graph state."""
        try:
            envelope = validate_event(raw_event)
        except ValidationError as exc:
            LOGGER.warning("task.received ignored (invalid envelope): %s", exc)
            return

        payload = envelope.payload or {}
        task_description = payload.get("task_description")
        execution_requested = bool(payload.get("execution_requested"))
        suppress_user_turn = bool(payload.get("suppress_user_turn"))
        if isinstance(task_description, str):
            task_description = task_description.strip()
        else:
            task_description = ""
        if not task_description and not execution_requested:
            LOGGER.warning("task.received ignored (missing task_description)")
            return

        project_id = envelope.project_id
        if not project_id:
            active = await self.project_manager.active_project()
            project_id = active.project_id if active else None

        if not project_id:
            LOGGER.error("task.received: no project_id and no active project")
            await self.event_bus.emit(
                "error.occurred",
                new_event(
                    "error.occurred",
                    payload={
                        "reason": "no_project",
                        "detail": "Select a project (/project use) or ensure one exists in the database.",
                    },
                    project_id=None,
                ).model_dump(),
            )
            return

        thread_state = await self._state_for_thread(envelope.thread_id)
        if (
            thread_state
            and thread_state.get("planning_status") not in TERMINAL_TASK_STATUSES
            and (thread_state.get("planning_thread_id") == envelope.thread_id or thread_state.get("current_thread_id") == envelope.thread_id)
        ):
            project_id = thread_state.get("project_id") or project_id

        await self.repository.initialize()
        project = await self.repository.get_project(project_id)
        if project is None:
            LOGGER.error("task.received: project not found: %s", project_id)
            await self.event_bus.emit(
                "error.occurred",
                new_event(
                    "error.occurred",
                    payload={"reason": "unknown_project", "project_id": project_id},
                    project_id=project_id,
                ).model_dump(),
            )
            return

        if self.graph is None:
            LOGGER.warning("task.received dropped: graph runtime not bootstrapped yet")
            await self.event_bus.emit(
                "error.occurred",
                new_event(
                    "error.occurred",
                    payload={"reason": "graph_not_ready", "detail": "Daemon startup not finished."},
                    project_id=project_id,
                ).model_dump(),
            )
            return

        existing_state = thread_state if thread_state.get("project_id") == project_id else await self.state_manager.get(project_id, {})
        if not isinstance(existing_state, dict):
            existing_state = {}
        if not existing_state and envelope.thread_id:
            config = self._thread_configs.get(envelope.thread_id) or build_thread_config(envelope.thread_id)
            snapshot = await self.graph.aget_state(config)
            checkpoint_state = dict(snapshot.values) if snapshot is not None and snapshot.values else {}
            if checkpoint_state.get("planning_status") not in TERMINAL_TASK_STATUSES:
                existing_state = checkpoint_state
                project_id = checkpoint_state.get("project_id") or project_id
                project = await self.repository.get_project(project_id) or project
        existing_is_terminal = existing_state.get("planning_status") in TERMINAL_TASK_STATUSES
        if existing_is_terminal:
            thread_id = envelope.thread_id or f"thread-{uuid4().hex}"
        else:
            thread_id = (
                existing_state.get("planning_thread_id")
                or existing_state.get("current_thread_id")
                or envelope.thread_id
                or f"thread-{uuid4().hex}"
            )
        config = self._thread_configs.get(thread_id) or build_thread_config(thread_id)
        self.register_project_thread(project_id, thread_id, config)
        try:
            if existing_state and not existing_is_terminal and self.project_id_for_thread(thread_id) == project_id:
                state_update = {
                    "project_id": project_id,
                    "project_name": project.name,
                    "task_description": task_description or existing_state.get("task_description", ""),
                    "execution_requested": execution_requested,
                    "suppress_user_turn": suppress_user_turn,
                    "planning_thread_id": thread_id,
                    "current_thread_id": thread_id,
                }
                await self.graph.aupdate_state(config, state_update, as_node="planner")
                await self.graph.ainvoke(Command(goto="planner"), config=config)
            else:
                initial = build_initial_state(
                    project_name=project.name,
                    task_description=task_description,
                    project_id=project_id,
                    current_thread_id=thread_id,
                )
                initial["execution_requested"] = execution_requested
                initial["suppress_user_turn"] = suppress_user_turn
                initial["planning_thread_id"] = thread_id
                await self.graph.ainvoke(initial, config=config)
            snapshot = await self.graph.aget_state(config)
            values = dict(snapshot.values)
            await self.state_manager.set(project_id, values)
            await self.state_manager.flush_to_disk()
            await self._emit_snapshot_sync(project_id, thread_id, phase="plan_ready")
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("task.received graph execution failed")
            await self.event_bus.emit(
                "error.occurred",
                new_event(
                    "error.occurred",
                    payload={"reason": "graph_invoke_failed", "detail": str(exc)},
                    project_id=project_id,
                    thread_id=thread_id,
                ).model_dump(),
            )

    async def bootstrap_runtime(self) -> None:
        await self.repository.initialize()
        if self.graph is not None:
            return
        self._runtime_cm = self.graph_runtime_factory(self.checkpoint_path)
        self.graph = await self._runtime_cm.__aenter__()
        LOGGER.info("Graph runtime bootstrapped at %s", self.checkpoint_path)

    async def shutdown_runtime(self) -> None:
        if self._runtime_cm is None:
            return
        await self.state_manager.flush_to_disk()
        await self._runtime_cm.__aexit__(None, None, None)
        self._runtime_cm = None
        self.graph = None
        LOGGER.info("Graph runtime shut down cleanly.")

    async def register_approval(self, approval_request: ApprovalRequest) -> None:
        await self.approval_guard.register_approval(approval_request)

    def attach_graph(self, graph: Any) -> None:
        self.graph = graph

    def register_thread(self, thread_id: str, config: dict[str, Any] | None = None) -> None:
        self._thread_configs[thread_id] = config or build_thread_config(thread_id)

    def register_project_thread(self, project_id: str, thread_id: str, config: dict[str, Any] | None = None) -> None:
        self.register_thread(thread_id, config)
        self._project_threads.setdefault(project_id, set()).add(thread_id)
        self._thread_projects[thread_id] = project_id
        self.scheduler.register_project(project_id)

    def thread_ids_for_project(self, project_id: str) -> list[str]:
        return sorted(self._project_threads.get(project_id, set()))

    def project_id_for_thread(self, thread_id: str) -> str | None:
        return self._thread_projects.get(thread_id)

    async def list_checkpoint_threads(self) -> list[str]:
        if not await aiofiles.ospath.exists(self.checkpoint_path):
            return []
        try:
            async with aiosqlite.connect(self.checkpoint_path) as connection:
                cursor = await connection.execute(
                    "SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id ASC"
                )
                rows = await cursor.fetchall()
        except aiosqlite.OperationalError:
            return []
        return [row[0] for row in rows if row and row[0]]

    async def recover_pending_threads(self) -> dict[str, Any]:
        await self.repository.initialize()
        recovered_threads: list[dict[str, Any]] = []
        orphan_cleanup = await self.cleanup_orphan_reservations()
        thread_ids = await self.list_checkpoint_threads()
        for thread_id in thread_ids:
            if self.graph is None:
                break
            config = build_thread_config(thread_id)
            self.register_thread(thread_id, config)
            snapshot = await self.graph.aget_state(config)
            if snapshot is None:
                continue
            state = dict(snapshot.values)
            project_id = state.get("project_id")
            if not project_id:
                continue
            self.register_project_thread(project_id, thread_id, config)
            await self.state_manager.set(project_id, state)
            if state.get("approval_request"):
                try:
                    approval_request = ApprovalRequest.model_validate(state["approval_request"])
                except ValidationError:
                    approval_request = None
                if approval_request is not None:
                    await self.register_approval(approval_request)
            recovered_threads.append(
                {
                    "thread_id": thread_id,
                    "project_id": project_id,
                    "awaiting_approval": bool(state.get("awaiting_approval")),
                    "next": list(snapshot.next),
                }
            )
        await self.state_manager.flush_to_disk()
        payload = {
            "recovered_threads": recovered_threads,
            "orphan_cleanup_count": orphan_cleanup,
        }
        snapshot = await self.state_manager.snapshot()
        for project_id, state in snapshot.items():
            if not isinstance(state, dict):
                continue
            approval_payload = state.get("approval_request")
            thread_id = state.get("planning_thread_id") or state.get("current_thread_id")
            if project_id and thread_id:
                self.register_project_thread(project_id, thread_id, self._thread_configs.get(thread_id))
            if isinstance(approval_payload, dict):
                try:
                    approval_request = ApprovalRequest.model_validate(approval_payload)
                except ValidationError:
                    continue
                await self.register_approval(approval_request)
        if recovered_threads or orphan_cleanup:
            await self.event_bus.emit(
                "system.recovered",
                new_event(
                    "system.recovered",
                    payload=payload,
                    project_id=recovered_threads[0]["project_id"] if recovered_threads else None,
                    thread_id=recovered_threads[0]["thread_id"] if recovered_threads else None,
                ).model_dump(),
            )
        LOGGER.info(
            "Recovery completed. threads=%s orphan_cleanup=%s",
            len(recovered_threads),
            orphan_cleanup,
        )
        return payload

    async def cleanup_orphan_reservations(self) -> int:
        snapshot = await self.state_manager.snapshot()
        active_files_by_project: dict[str, set[str]] = {}
        for state in snapshot.values():
            if not isinstance(state, dict):
                continue
            project_id = state.get("project_id")
            if not project_id:
                continue
            active_files = active_files_by_project.setdefault(project_id, set())
            active_assignment = state.get("active_assignment")
            if isinstance(active_assignment, dict) and active_assignment.get("target_file"):
                active_files.add(active_assignment["target_file"])
            for assignment in state.get("active_assignments", {}).values():
                if isinstance(assignment, dict) and assignment.get("target_file"):
                    active_files.add(assignment["target_file"])

        cleaned = 0
        for project in await self.repository.list_projects():
            file_records = await self.repository.list_file_records(project.project_id)
            project_state = await self.state_manager.get(project.project_id, {})
            if not isinstance(project_state, dict):
                project_state = {}
            registry = deepcopy(project_state.get("file_registry", {}))
            for record in file_records:
                if record.status != "reserved":
                    continue
                if record.path in active_files_by_project.get(project.project_id, set()):
                    continue
                updated = record.model_copy(
                    update={
                        "status": "planned",
                        "worker_id": None,
                        "reservation_owner": None,
                        "updated_at": utc_now(),
                    }
                )
                await self.repository.upsert_file_record(updated)
                if registry.get(record.path) == "reserved":
                    registry[record.path] = "planned"
                cleaned += 1
            if registry:
                await self.state_manager.update(project.project_id, {"file_registry": registry})
        if cleaned:
            await self.state_manager.flush_to_disk()
        return cleaned

    async def schedule_project_thread(self, *, project_id: str, thread_id: str, task_id: str, payload: dict[str, Any] | None = None) -> None:
        self.register_project_thread(project_id, thread_id)
        self.scheduler.enqueue(
            ScheduledTask(
                project_id=project_id,
                thread_id=thread_id,
                task_id=task_id,
                payload=payload or {},
            )
        )

    async def next_scheduled_thread(self) -> dict[str, Any] | None:
        decision = self.scheduler.acquire_next()
        if decision.task is None:
            return None
        return {
            "project_id": decision.task.project_id,
            "thread_id": decision.task.thread_id,
            "task_id": decision.task.task_id,
            "payload": decision.task.payload,
        }

    async def release_project_slot(self, project_id: str) -> None:
        self.scheduler.release(project_id)

    async def archive_project(self, project_id: str) -> None:
        self.scheduler.archive_project(project_id)
        await self.project_manager.archive_project(project_id)

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
        await self._handle_decision_event(raw_event, expected_event_type="plan.approved")

    async def on_plan_rejected(self, raw_event: dict[str, Any]) -> None:
        await self._handle_decision_event(raw_event, expected_event_type="plan.rejected")

    async def on_plan_cancelled(self, raw_event: dict[str, Any]) -> None:
        await self._handle_decision_event(raw_event, expected_event_type="plan.cancelled")

    async def _handle_decision_event(
        self,
        raw_event: dict[str, Any],
        *,
        expected_event_type: str,
    ) -> ApprovalConsumeResult:
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
        if envelope.event_id in self._processed_event_ids:
            return ApprovalConsumeResult(
                outcome="no-op",
                reason="duplicate_event_id",
                approval_id=envelope.payload.get("approval_id", "unknown"),
            )
        if envelope.idempotency_key in self._processed_idempotency_keys:
            return ApprovalConsumeResult(
                outcome="no-op",
                reason="duplicate_idempotency_key",
                approval_id=envelope.payload.get("approval_id", "unknown"),
            )

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

        self._processed_event_ids.add(envelope.event_id)
        self._processed_idempotency_keys.add(envelope.idempotency_key)

        async with StateTransaction(decision.project_id, self.state_manager) as transaction:
            state = transaction.state
            approvals = state.setdefault("approvals", {})
            approvals[decision.approval_id] = {
                "decision": decision.decision,
                "idempotency_key": decision.idempotency_key,
                "thread_id": decision.thread_id,
                "sprint_id": decision.sprint_id,
            }
            transaction.state = state

        await self.state_manager.flush_to_disk()
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
                "approval_request": None,
                "planning_status": "approved_for_execution",
                "execution_requested": False,
                "messages": [*snapshot.values.get("messages", []), f"approval accepted for {decision.approval_id}"],
            },
            as_node="planner",
        )
        await self.graph.ainvoke(Command(goto="dispatcher"), config=config)
        refreshed = await self.graph.aget_state(config)
        await self.state_manager.set(decision.project_id, refreshed.values)
        await self.state_manager.flush_to_disk()
        await self._emit_snapshot_sync(decision.project_id, decision.thread_id, phase="post_approval")

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
                "approval_request": None,
                "planning_status": terminal_status,
                "execution_requested": False,
                "sprint_status": "fail",
                "errors": [*snapshot.values.get("errors", []), {"type": terminal_status, "approval_id": decision.approval_id}],
                "messages": [*snapshot.values.get("messages", []), f"approval {terminal_status} for {decision.approval_id}"],
            },
            as_node="planner",
        )
        refreshed = await self.graph.aget_state(config)
        await self.state_manager.set(decision.project_id, refreshed.values)
        await self.state_manager.flush_to_disk()
        await self._emit_snapshot_sync(decision.project_id, decision.thread_id, phase=f"stopped_{terminal_status}")
