from __future__ import annotations

from copy import deepcopy

from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.state_transaction import StateTransaction


async def reviewer_node(state: dict) -> dict:
    project_id = state["project_id"]
    thread_id = state["current_thread_id"]
    sprint_id = f"sprint-{state.get('current_sprint', 1)}"
    queue = deepcopy(state.get("worker_queue", []))
    file_registry = deepcopy(state.get("file_registry", {}))
    validation_issues = deepcopy(state.get("validation_issues", []))
    review_cycles = state.get("review_cycles", 0) + 1

    await EventBus().emit(
        "sprint.review_started",
        new_event(
            "sprint.review_started",
            payload={"review_cycles": review_cycles},
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
            correlation_id=project_id,
        ).model_dump(),
    )

    pending_items = [item for item in queue if item.get("status") == "planned"]
    if validation_issues:
        if review_cycles >= 3:
            await EventBus().emit(
                "sprint.completed",
                new_event(
                    "sprint.completed",
                    payload={"result": "fail", "issues": validation_issues},
                    project_id=project_id,
                    thread_id=thread_id,
                    sprint_id=sprint_id,
                    correlation_id=project_id,
                ).model_dump(),
            )
            updates = {
                "sprint_status": "fail",
                "review_cycles": review_cycles,
                "errors": [*state.get("errors", []), *validation_issues],
                "messages": [*state.get("messages", []), "reviewer failed after max cycles"],
            }
        else:
            for issue in validation_issues:
                for item in queue:
                    if item["assignment"]["target_file"] == issue["target_file"]:
                        item["status"] = "planned"
                        item["validation_error"] = issue["issue"]
                        file_registry[issue["target_file"]] = "planned"
            await EventBus().emit(
                "sprint.revision_needed",
                new_event(
                    "sprint.revision_needed",
                    payload={"issues": validation_issues},
                    project_id=project_id,
                    thread_id=thread_id,
                    sprint_id=sprint_id,
                    correlation_id=project_id,
                ).model_dump(),
            )
            updates = {
                "worker_queue": queue,
                "file_registry": file_registry,
                "sprint_status": "revision",
                "review_cycles": review_cycles,
                "messages": [*state.get("messages", []), "reviewer requested revision"],
            }
    elif pending_items:
        updates = {
            "sprint_status": "active",
            "review_cycles": review_cycles,
            "messages": [*state.get("messages", []), "reviewer found pending work"],
        }
    elif all(status == "done" for status in file_registry.values()):
        await EventBus().emit(
            "sprint.completed",
            new_event(
                "sprint.completed",
                payload={"result": "approved", "files": list(file_registry.keys())},
                project_id=project_id,
                thread_id=thread_id,
                sprint_id=sprint_id,
                correlation_id=project_id,
            ).model_dump(),
        )
        updates = {
            "sprint_status": "approved",
            "review_cycles": review_cycles,
            "messages": [*state.get("messages", []), "reviewer approved sprint"],
            "validation_issues": [],
            "revision_tasks": [],
        }
    else:
        updates = {
            "sprint_status": "fail",
            "review_cycles": review_cycles,
            "errors": [
                *state.get("errors", []),
                {"type": "review_deadlock", "message": "No pending items completed successfully."},
            ],
            "messages": [*state.get("messages", []), "reviewer detected deadlock"],
        }

    async with StateTransaction(project_id) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted
    return updates
