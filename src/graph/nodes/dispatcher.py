from __future__ import annotations

from copy import deepcopy

from src.core.contracts import DispatchAssignment, new_event
from src.core.event_bus import EventBus
from src.core.state_transaction import StateTransaction


async def dispatcher_node(state: dict) -> dict:
    queue = deepcopy(state.get("worker_queue", []))
    dependencies = deepcopy(state.get("dependencies", {}))
    file_registry = deepcopy(state.get("file_registry", {}))
    worker_status = deepcopy(state.get("worker_status", {}))
    project_id = state["project_id"]
    thread_id = state["current_thread_id"]
    sprint_id = f"sprint-{state.get('current_sprint', 1)}"

    if state.get("active_assignment") is not None:
        return {
            "messages": [*state.get("messages", []), "dispatcher detected active assignment"],
        }

    idle_worker = next((worker_id for worker_id, status in worker_status.items() if status == "idle"), None)
    if idle_worker is None:
        return {
            "messages": [*state.get("messages", []), "dispatcher found no idle worker"],
        }

    selected_index: int | None = None
    selected_assignment: dict | None = None
    for index, item in enumerate(queue):
        if item.get("status") != "planned":
            continue
        assignment = DispatchAssignment.model_validate(item["assignment"]).model_copy(update={"worker_id": idle_worker})
        target_file = assignment.target_file
        deps = dependencies.get(target_file, [])
        if all(file_registry.get(dep) == "done" for dep in deps):
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
                },
            ],
        }

    target_file = selected_assignment["target_file"]
    queue[selected_index]["assignment"] = selected_assignment
    queue[selected_index]["status"] = "assigned"
    file_registry[target_file] = "reserved"
    worker_status[idle_worker] = "reserved"

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

    updates = {
        "worker_queue": queue,
        "file_registry": file_registry,
        "worker_status": worker_status,
        "active_assignment": selected_assignment,
        "messages": [*state.get("messages", []), f"dispatcher assigned {target_file} to {idle_worker}"],
    }
    async with StateTransaction(project_id) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted

    return updates
