from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from src.core.contracts import ApprovalRequest, DispatchAssignment, new_event
from src.core.event_bus import EventBus
from src.core.state_transaction import StateTransaction


async def planner_node(state: dict) -> dict:
    project_id = state["project_id"]
    thread_id = state["current_thread_id"]
    sprint_id = f"sprint-{state.get('current_sprint', 1)}"

    queue = [
        {
            "assignment": DispatchAssignment(
                task_id=str(uuid4()),
                project_id=project_id,
                thread_id=thread_id,
                sprint_id=sprint_id,
                worker_id="",
                target_file="helpers.py",
                description="Create a helper function for the generated project.",
                correlation_id=project_id,
                metadata={"kind": "python"},
            ).model_dump(),
            "status": "planned",
            "validation_error": None,
        },
        {
            "assignment": DispatchAssignment(
                task_id=str(uuid4()),
                project_id=project_id,
                thread_id=thread_id,
                sprint_id=sprint_id,
                worker_id="",
                target_file="app.py",
                description="Create the application entry that uses helpers.",
                correlation_id=project_id,
                metadata={"kind": "python"},
            ).model_dump(),
            "status": "planned",
            "validation_error": None,
        },
    ]
    dependencies = {
        "helpers.py": [],
        "app.py": ["helpers.py"],
    }
    file_registry = {target_file: "planned" for target_file in dependencies}
    approval_request = ApprovalRequest(
        approval_id=str(uuid4()),
        project_id=project_id,
        thread_id=thread_id,
        sprint_id=sprint_id,
        approval_type="plan",
        reason="Planner generated the initial dependency-aware sprint plan.",
        metadata={
            "files": list(file_registry.keys()),
            "dependencies": deepcopy(dependencies),
        },
    )
    context_summary = (
        f"Project={state['project_name']} | Sprint={state.get('current_sprint', 1)} | "
        f"Task={state['task_description']} | Files={', '.join(file_registry.keys())}"
    )

    await EventBus().emit(
        "plan.generated",
        new_event(
            "plan.generated",
            payload={
                "project_id": project_id,
                "sprint_id": sprint_id,
                "files": list(file_registry.keys()),
            },
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
            correlation_id=project_id,
        ).model_dump(),
    )
    await EventBus().emit(
        "plan.approval_needed",
        new_event(
            "plan.approval_needed",
            payload=approval_request.model_dump(),
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
            correlation_id=project_id,
            idempotency_key=approval_request.approval_id,
        ).model_dump(),
    )

    updates = {
        "worker_queue": queue,
        "dependencies": dependencies,
        "file_registry": file_registry,
        "worker_status": state.get("worker_status", {"worker_a": "idle"}),
        "worker_outputs": state.get("worker_outputs", {"worker_a": []}),
        "worker_failure_log": state.get("worker_failure_log", {"worker_a": []}),
        "current_sprint": state.get("current_sprint", 1),
        "sprint_type": "feature",
        "sprint_status": "planning",
        "awaiting_approval": True,
        "approval_type": "plan",
        "active_approval_id": approval_request.approval_id,
        "approval_request": approval_request.model_dump(),
        "context_summary": context_summary,
        "messages": [*state.get("messages", []), "planner completed"],
        "errors": state.get("errors", []),
        "validation_issues": [],
        "revision_tasks": [],
        "active_assignment": None,
    }

    async with StateTransaction(project_id) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted

    return updates
