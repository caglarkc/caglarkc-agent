from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from src.config.settings import get_settings
from src.core.context_builder import ContextBuilder
from src.core.contracts import ApprovalRequest, PlanConversationTurn, new_event
from src.core.event_bus import EventBus
from src.core.manager_planning import ManagerPlanningService, draft_to_queue
from src.core.project_manager import ProjectManager
from src.core.state_transaction import StateTransaction
from src.storage.models import FileRecord, Project, Sprint
from src.storage.repository import Repository


def _contract_queue(project_id: str, thread_id: str, sprint_id: str) -> tuple[list[dict], dict[str, list[str]]]:
    files = [
        ("api_contract.json", "Define the initial API contract for the project.", "contract_spec"),
        ("shared_types.py", "Define shared data models used across the project.", "shared_types"),
        ("src/__init__.py", "Create the initial package scaffold.", "scaffold"),
    ]
    queue = []
    dependencies = {
        "api_contract.json": [],
        "shared_types.py": ["api_contract.json"],
        "src/__init__.py": ["shared_types.py"],
    }
    for target_file, description, task_type in files:
        queue.append(
            {
                "assignment": {
                    "task_id": str(uuid4()),
                    "project_id": project_id,
                    "thread_id": thread_id,
                    "sprint_id": sprint_id,
                    "worker_id": "unassigned",
                    "target_file": target_file,
                    "description": description,
                    "correlation_id": project_id,
                    "metadata": {"kind": "contract", "task_type": task_type},
                },
                "status": "planned",
                "validation_error": None,
                "retry_count": 0,
                "blocked_by": [],
                "task_type": task_type,
            }
        )
    return queue, dependencies


def _feature_queue(project_id: str, thread_id: str, sprint_id: str) -> tuple[list[dict], dict[str, list[str]]]:
    files = [
        ("helpers.py", "Create a helper function for the generated project.", "feature_helper"),
        ("app.py", "Create the application entry that uses helpers.", "feature_entry"),
    ]
    queue = []
    dependencies = {"helpers.py": [], "app.py": ["helpers.py"]}
    for target_file, description, task_type in files:
        queue.append(
            {
                "assignment": {
                    "task_id": str(uuid4()),
                    "project_id": project_id,
                    "thread_id": thread_id,
                    "sprint_id": sprint_id,
                    "worker_id": "unassigned",
                    "target_file": target_file,
                    "description": description,
                    "correlation_id": project_id,
                    "metadata": {"kind": "feature", "task_type": task_type},
                },
                "status": "planned",
                "validation_error": None,
                "retry_count": 0,
                "blocked_by": [],
                "task_type": task_type,
            }
        )
    return queue, dependencies


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


async def planner_node(state: dict) -> dict:
    settings = get_settings()
    if settings.use_legacy_planner:
        return await _legacy_planner_node(state)
    return await _manager_planner_node(state)


async def _manager_planner_node(state: dict) -> dict:
    project_id = state["project_id"]
    thread_id = state["current_thread_id"]
    repository = Repository()
    project_manager = ProjectManager()
    await repository.initialize()
    current_sprint = state.get("current_sprint", 1)
    plan_version = state.get("plan_version", 1) + (1 if state.get("scope_changed") else 0)
    sprint_id = f"sprint-{current_sprint}"
    conversation_history = list(state.get("conversation_history", []))
    current_message = str(state.get("task_description", "") or "").strip()
    if current_message and not state.get("suppress_user_turn"):
        user_turn = PlanConversationTurn(role="user", content=current_message).model_dump()
        if not conversation_history or conversation_history[-1].get("role") != "user" or conversation_history[-1].get("content") != current_message:
            conversation_history.append(user_turn)

    planning_result = await ManagerPlanningService().process_turn(
        user_message=current_message,
        conversation_history=conversation_history,
        existing_draft=state.get("draft_plan"),
        explicit_execution=bool(state.get("execution_requested")),
    )
    if planning_result.reply_text:
        conversation_history.append(PlanConversationTurn(role="manager", content=planning_result.reply_text).model_dump())

    draft_plan = planning_result.draft_plan.model_dump() if planning_result.draft_plan else state.get("draft_plan")
    worker_queue: list[dict] = []
    dependencies: dict[str, list[str]] = {}
    file_registry: dict[str, str] = {}
    file_list: list[str] = []
    planned_worker_queue: list[dict] = []
    planned_dependencies: dict[str, list[str]] = {}
    planned_file_registry: dict[str, str] = {}
    approval_request = None
    awaiting_approval = False
    approval_type = ""
    active_approval_id = None
    sprint_status = "planning"
    planning_status = "conversation"
    context_summary = await ContextBuilder(repository=repository, project_manager=project_manager).build(
        project_id,
        state["project_name"],
    )

    await repository.upsert_project(
        Project(
            project_id=project_id,
            name=state["project_name"],
            description=current_message or state.get("task_description", ""),
            status="active",
            metadata={
                "contract_completed": state.get("contract_completed", False),
                "planning_thread_id": thread_id,
            },
        )
    )

    if planning_result.draft_plan is not None:
        planned_worker_queue, planned_dependencies, planned_file_registry = draft_to_queue(
            planning_result.draft_plan,
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
        )
        file_list = list(planned_file_registry.keys())
        await EventBus().emit(
            "plan.draft_updated",
            new_event(
                "plan.draft_updated",
                payload={
                    "project_id": project_id,
                    "summary": planning_result.draft_plan.summary,
                    "files": file_list,
                    "sprint_type": planning_result.draft_plan.sprint_type,
                },
                project_id=project_id,
                thread_id=thread_id,
                sprint_id=sprint_id,
                correlation_id=project_id,
            ).model_dump(),
        )

    if planning_result.execution_intent.mode == "apply" and planning_result.draft_plan is not None:
        worker_queue = planned_worker_queue
        dependencies = planned_dependencies
        file_registry = planned_file_registry
        if _detect_cycle(dependencies):
            return {
                "sprint_status": "fail",
                "errors": [{"type": "dependency_cycle", "dependencies": dependencies}],
                "messages": ["planner detected dependency cycle"],
                "conversation_history": conversation_history,
                "manager_reply": planning_result.reply_text,
                "planning_status": "invalid_plan",
                "execution_requested": False,
            }
        sprint_record = Sprint(
            sprint_id=str(uuid4()),
            project_id=project_id,
            number=current_sprint,
            sprint_type=planning_result.draft_plan.sprint_type,
            status="planning",
            plan_version=plan_version,
            decisions=["manager_plan"],
        )
        await repository.create_sprint(sprint_record)
        for target_file in file_registry:
            await repository.upsert_file_record(
                FileRecord(
                    file_id=str(uuid4()),
                    project_id=project_id,
                    sprint_id=sprint_record.sprint_id,
                    path=target_file,
                    status="planned",
                )
            )

        approval_request = ApprovalRequest(
            approval_id=str(uuid4()),
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
            approval_type="plan",
            reason=f"Manager generated a {planning_result.draft_plan.sprint_type} sprint plan.",
            metadata={
                "plan_summary": planning_result.draft_plan.summary,
                "files": file_list,
                "dependencies": deepcopy(dependencies),
                "sprint_type": planning_result.draft_plan.sprint_type,
                "plan_version": plan_version,
                "source": "gemini_manager",
            },
        )
        await EventBus().emit(
            "plan.generated",
            new_event(
                "plan.generated",
                payload={
                    "project_id": project_id,
                    "sprint_id": sprint_id,
                    "files": file_list,
                    "sprint_type": planning_result.draft_plan.sprint_type,
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
        awaiting_approval = True
        approval_type = "plan"
        active_approval_id = approval_request.approval_id
        planning_status = "awaiting_approval"
        context_summary = (
            f"{context_summary}\nPlanned Sprint Type: {planning_result.draft_plan.sprint_type} | "
            f"Files: {', '.join(file_list)}"
        )
        await project_manager.update_plan_snapshot(
            state["project_name"],
            sprint_number=current_sprint,
            sprint_type=planning_result.draft_plan.sprint_type,
            status="planning",
            files=file_list,
            dependencies=dependencies,
            plan_version=plan_version,
            scope_changed=bool(state.get("last_scope_change")),
        )
    else:
        planning_status = "needs_input" if planning_result.needs_clarification else "draft_ready"

    await EventBus().emit(
        "manager.reply",
        new_event(
            "manager.reply",
            payload={
                "project_id": project_id,
                "reply_text": planning_result.reply_text,
                "planning_status": planning_status,
                "has_draft_plan": bool(draft_plan),
            },
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
            correlation_id=project_id,
        ).model_dump(),
    )

    updates = {
        "worker_queue": worker_queue,
        "dependencies": dependencies,
        "file_registry": file_registry,
        "worker_status": state.get("worker_status", {"worker_a": "idle", "worker_b": "idle", "worker_c": "idle"}),
        "worker_outputs": state.get("worker_outputs", {"worker_a": [], "worker_b": [], "worker_c": []}),
        "worker_failure_log": state.get("worker_failure_log", {"worker_a": [], "worker_b": [], "worker_c": []}),
        "current_sprint": current_sprint,
        "sprint_type": planning_result.draft_plan.sprint_type if planning_result.draft_plan else state.get("sprint_type", "feature"),
        "sprint_status": sprint_status,
        "awaiting_approval": awaiting_approval,
        "approval_type": approval_type,
        "active_approval_id": active_approval_id,
        "approval_request": approval_request.model_dump() if approval_request else None,
        "context_summary": context_summary,
        "manager_reply": planning_result.reply_text,
        "conversation_history": conversation_history,
        "draft_plan": draft_plan,
        "planning_status": planning_status,
        "planning_thread_id": thread_id,
        "execution_requested": False,
        "suppress_user_turn": False,
        "messages": ["planner completed"],
        "errors": [],
        "validation_issues": [],
        "revision_tasks": [],
        "active_assignment": None,
        "active_assignments": {},
        "blocked_reasons": [],
        "plan_version": plan_version,
        "last_scope_change": (
            {"reason": state.get("scope_change_reason", "external_requirement"), "handled": True}
            if state.get("scope_changed")
            else state.get("last_scope_change")
        ),
        "scope_changed": False,
    }
    async with StateTransaction(project_id) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted
    return updates


async def _legacy_planner_node(state: dict) -> dict:
    project_id = state["project_id"]
    thread_id = state["current_thread_id"]
    repository = Repository()
    project_manager = ProjectManager()
    await repository.initialize()
    current_sprint = state.get("current_sprint", 1)
    plan_version = state.get("plan_version", 1) + (1 if state.get("scope_changed") else 0)
    sprint_id = f"sprint-{current_sprint}"
    requested_feature = state.get("requested_sprint_type") == "feature"
    sprint_type = "contract" if current_sprint == 1 and not state.get("contract_completed") else "feature"
    if requested_feature and sprint_type == "contract":
        state_messages = ["feature sprint request gated until contract sprint completes"]
    else:
        state_messages = []

    if sprint_type == "contract":
        queue, dependencies = _contract_queue(project_id, thread_id, sprint_id)
    else:
        queue, dependencies = _feature_queue(project_id, thread_id, sprint_id)

    if state.get("scope_changed"):
        for item in queue:
            item["status"] = "planned"
        state_messages.append("planner replanned due to scope change")

    if _detect_cycle(dependencies):
        updates = {
            "sprint_status": "fail",
            "errors": [{"type": "dependency_cycle", "dependencies": dependencies}],
            "messages": [*state_messages, "planner detected dependency cycle"],
        }
        async with StateTransaction(project_id) as transaction:
            persisted = transaction.state
            persisted.update(updates)
            transaction.state = persisted
        return updates

    file_registry = {target_file: "planned" for target_file in dependencies}
    await repository.upsert_project(
        Project(
            project_id=project_id,
            name=state["project_name"],
            description=state["task_description"],
            status="active",
            metadata={"contract_completed": state.get("contract_completed", False)},
        )
    )
    sprint_record = Sprint(
        sprint_id=str(uuid4()),
        project_id=project_id,
        number=current_sprint,
        sprint_type=sprint_type,
        status="planning",
        plan_version=plan_version,
        decisions=["scope_changed" if state.get("scope_changed") else "initial_plan"],
    )
    await repository.create_sprint(sprint_record)
    for target_file in file_registry:
        await repository.upsert_file_record(
            FileRecord(
                file_id=str(uuid4()),
                project_id=project_id,
                sprint_id=sprint_record.sprint_id,
                path=target_file,
                status="planned",
            )
        )

    approval_request = ApprovalRequest(
        approval_id=str(uuid4()),
        project_id=project_id,
        thread_id=thread_id,
        sprint_id=sprint_id,
        approval_type="plan",
        reason=f"Planner generated a {sprint_type} sprint plan.",
        metadata={
            "files": list(file_registry.keys()),
            "dependencies": deepcopy(dependencies),
            "sprint_type": sprint_type,
            "plan_version": plan_version,
        },
    )
    context_summary = await ContextBuilder(repository=repository, project_manager=project_manager).build(
        project_id,
        state["project_name"],
    )
    context_summary = (
        f"{context_summary}\nPlanned Sprint Type: {sprint_type} | "
        f"Files: {', '.join(file_registry.keys())}"
    )

    await EventBus().emit(
        "plan.generated",
        new_event(
            "plan.generated",
            payload={
                "project_id": project_id,
                "sprint_id": sprint_id,
                "files": list(file_registry.keys()),
                "sprint_type": sprint_type,
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
        "worker_status": state.get("worker_status", {"worker_a": "idle", "worker_b": "idle", "worker_c": "idle"}),
        "worker_outputs": state.get("worker_outputs", {"worker_a": [], "worker_b": [], "worker_c": []}),
        "worker_failure_log": state.get("worker_failure_log", {"worker_a": [], "worker_b": [], "worker_c": []}),
        "current_sprint": current_sprint,
        "sprint_type": sprint_type,
        "sprint_status": "planning",
        "awaiting_approval": True,
        "approval_type": "plan",
        "active_approval_id": approval_request.approval_id,
        "approval_request": approval_request.model_dump(),
        "context_summary": context_summary,
        "messages": [*state_messages, "planner completed"],
        "errors": [],
        "validation_issues": [],
        "revision_tasks": [],
        "active_assignment": None,
        "active_assignments": {},
        "blocked_reasons": [],
        "plan_version": plan_version,
        "last_scope_change": (
            {"reason": state.get("scope_change_reason", "external_requirement"), "handled": True}
            if state.get("scope_changed")
            else state.get("last_scope_change")
        ),
        "scope_changed": False,
    }
    await project_manager.update_plan_snapshot(
        state["project_name"],
        sprint_number=current_sprint,
        sprint_type=sprint_type,
        status="planning",
        files=list(file_registry.keys()),
        dependencies=dependencies,
        plan_version=plan_version,
        scope_changed=bool(state.get("last_scope_change")),
    )

    async with StateTransaction(project_id) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted

    return updates
