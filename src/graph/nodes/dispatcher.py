from __future__ import annotations

from datetime import datetime, timedelta, timezone
from copy import deepcopy
from uuid import uuid4

from src.core.contracts import DispatchAssignment, new_event
from src.core.event_bus import EventBus
from src.core.retry_policy import classify_error
from src.core.state_transaction import StateTransaction
from src.storage.models import FileRecord
from src.storage.repository import Repository


HEARTBEAT_INTERVAL_SECONDS = 60
STALL_TIMEOUT_SECONDS = 600
ACTIVE_ASSIGNMENT_GRACE_SECONDS = 180


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def should_emit_stalled(
    *,
    last_heartbeat_at: str | None,
    active_assignment: dict | None,
    now: datetime | None = None,
) -> bool:
    if not last_heartbeat_at:
        return False
    current_time = now or datetime.now(timezone.utc)
    last_seen = datetime.fromisoformat(last_heartbeat_at)
    grace = ACTIVE_ASSIGNMENT_GRACE_SECONDS if active_assignment else 0
    return current_time - last_seen > timedelta(seconds=STALL_TIMEOUT_SECONDS + grace)


def _detect_cycle(dependencies: dict[str, list[str]]) -> bool:
    visited: set[str] = set()
    active: set[str] = set()

    def visit(node: str) -> bool:
        if node in active:
            return True
        if node in visited:
            return False
        visited.add(node)
        active.add(node)
        for dep in dependencies.get(node, []):
            if visit(dep):
                return True
        active.remove(node)
        return False

    return any(visit(node) for node in dependencies)


async def dispatcher_node(state: dict) -> dict:
    repository = Repository()
    await repository.initialize()
    queue = deepcopy(state.get("worker_queue", []))
    dependencies = deepcopy(state.get("dependencies", {}))
    file_registry = deepcopy(state.get("file_registry", {}))
    worker_status = deepcopy(state.get("worker_status", {}))
    reservation_conflicts = deepcopy(state.get("reservation_conflicts", []))
    last_heartbeat_at = state.get("last_heartbeat_at")
    project_id = state["project_id"]
    thread_id = state["current_thread_id"]
    sprint_id = f"sprint-{state.get('current_sprint', 1)}"

    if state.get("scope_changed"):
        for item in queue:
            if item.get("status") in {"assigned", "in_progress"}:
                item["status"] = "planned"
        cleared_workers = {worker_id: "idle" for worker_id in worker_status}
        updates = {
            "worker_queue": queue,
            "worker_status": cleared_workers,
            "active_assignment": None,
            "sprint_status": "paused_replan",
            "messages": [*state.get("messages", []), "dispatcher paused active work for scope change"],
        }
        async with StateTransaction(project_id) as transaction:
            persisted = transaction.state
            persisted.update(updates)
            transaction.state = persisted
        return updates

    if state.get("active_assignment") is not None:
        if should_emit_stalled(
            last_heartbeat_at=last_heartbeat_at,
            active_assignment=state.get("active_assignment"),
        ):
            stalled_at = utc_now_iso()
            await EventBus().emit(
                "system.stalled",
                new_event(
                    "system.stalled",
                    payload={"reason": "active_assignment_silent", "project_id": project_id},
                    project_id=project_id,
                    thread_id=thread_id,
                    sprint_id=sprint_id,
                    correlation_id=project_id,
                ).model_dump(),
            )
            return {
                "stalled_since": stalled_at,
                "messages": [*state.get("messages", []), "dispatcher detected stalled active assignment"],
            }
        return {
            "messages": [*state.get("messages", []), "dispatcher detected active assignment"],
        }

    if _detect_cycle(dependencies):
        return {
            "sprint_status": "fail",
            "errors": [*state.get("errors", []), {"type": "dependency_cycle", "dependencies": dependencies}],
            "messages": [*state.get("messages", []), "dispatcher detected dependency cycle"],
        }

    idle_worker = next((worker_id for worker_id, status in worker_status.items() if status == "idle"), None)
    if idle_worker is None:
        if should_emit_stalled(
            last_heartbeat_at=last_heartbeat_at,
            active_assignment=state.get("active_assignment"),
        ):
            stalled_at = utc_now_iso()
            await EventBus().emit(
                "system.stalled",
                new_event(
                    "system.stalled",
                    payload={"reason": "no_worker_and_no_heartbeat", "project_id": project_id},
                    project_id=project_id,
                    thread_id=thread_id,
                    sprint_id=sprint_id,
                    correlation_id=project_id,
                ).model_dump(),
            )
            return {
                "stalled_since": stalled_at,
                "messages": [*state.get("messages", []), "dispatcher emitted stalled due to heartbeat silence"],
            }
        return {
            "messages": [*state.get("messages", []), "dispatcher found no idle worker"],
        }

    selected_index: int | None = None
    selected_assignment: dict | None = None
    blocked_reasons: list[dict] = []
    for index, item in enumerate(queue):
        if item.get("status") != "planned":
            continue
        assignment = DispatchAssignment.model_validate(item["assignment"]).model_copy(update={"worker_id": idle_worker})
        target_file = assignment.target_file
        deps = dependencies.get(target_file, [])
        unmet = [dep for dep in deps if file_registry.get(dep) != "done"]
        if unmet:
            blocked_reasons.append({"target_file": target_file, "reason": "waiting_dependencies", "dependencies": unmet})
            continue
        if file_registry.get(target_file) in {"reserved", "done", "in_progress"}:
            reservation_conflicts.append(
                {"target_file": target_file, "reason": f"file status is {file_registry.get(target_file)}"}
            )
            continue
        existing_record = await repository.get_file_record(project_id, target_file)
        if existing_record and existing_record.status in {"reserved", "done", "in_progress"}:
            reservation_conflicts.append(
                {"target_file": target_file, "reason": f"repository status is {existing_record.status}"}
            )
            continue
        selected_index = index
        selected_assignment = assignment.model_dump()
        break

    if selected_index is None or selected_assignment is None:
        pending = [entry["assignment"]["target_file"] for entry in queue if entry.get("status") == "planned"]
        return {
            "messages": [*state.get("messages", []), "dispatcher found no ready assignment"],
            "errors": [
                *state.get("errors", []),
                {
                    "type": "dispatch_blocked",
                    "pending_files": pending,
                    "blocked_reasons": blocked_reasons,
                },
            ],
            "blocked_reasons": blocked_reasons,
            "reservation_conflicts": reservation_conflicts,
        }

    target_file = selected_assignment["target_file"]
    queue[selected_index]["assignment"] = selected_assignment
    queue[selected_index]["status"] = "assigned"
    queue[selected_index]["blocked_by"] = []
    file_registry[target_file] = "reserved"
    worker_status[idle_worker] = "reserved"
    await repository.upsert_file_record(
        FileRecord(
            file_id=str(uuid4()),
            project_id=project_id,
            sprint_id=sprint_id,
            path=target_file,
            status="reserved",
            worker_id=idle_worker,
            reservation_owner=idle_worker,
        )
    )

    await EventBus().emit(
        "system.heartbeat",
        new_event(
            "system.heartbeat",
            payload={
                "task_id": selected_assignment["task_id"],
                "worker_id": idle_worker,
                "target_file": target_file,
            },
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
            correlation_id=selected_assignment["task_id"],
        ).model_dump(),
    )
    heartbeat_at = utc_now_iso()

    updates = {
        "worker_queue": queue,
        "file_registry": file_registry,
        "worker_status": worker_status,
        "active_assignment": selected_assignment,
        "blocked_reasons": blocked_reasons,
        "reservation_conflicts": reservation_conflicts,
        "last_heartbeat_at": heartbeat_at,
        "last_activity_at": heartbeat_at,
        "stalled_since": None,
        "messages": [*state.get("messages", []), f"dispatcher assigned {target_file} to {idle_worker}"],
    }
    async with StateTransaction(project_id) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted

    return updates
