from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict
from uuid import uuid4


FileStatus = Literal["planned", "reserved", "in_progress", "done", "failed"]


class QueueEntry(TypedDict, total=False):
    assignment: dict[str, Any]
    status: str
    validation_error: str | None
    retry_count: int
    blocked_by: list[str]
    task_type: str


class OrchestratorState(TypedDict, total=False):
    project_id: str
    project_name: str
    task_description: Annotated[str, lambda a, b: b]
    worker_queue: list[QueueEntry]
    dependencies: dict[str, list[str]]
    file_registry: dict[str, FileStatus]
    worker_status: dict[str, str]
    worker_outputs: dict[str, list[str]]
    worker_failure_log: dict[str, list[dict[str, Any]]]
    current_sprint: int
    sprint_type: str
    sprint_status: str
    review_cycles: int
    awaiting_approval: bool
    approval_type: str
    active_approval_id: str | None
    context_summary: str
    manager_reply: str | None
    draft_plan: dict[str, Any] | None
    conversation_history: list[dict[str, Any]]
    planning_status: str
    execution_requested: Annotated[bool, lambda a, b: b]
    suppress_user_turn: Annotated[bool, lambda a, b: b]
    planning_thread_id: Annotated[str | None, lambda a, b: b]
    scope_changed: bool
    errors: Annotated[list[dict[str, Any]], operator.add]
    messages: Annotated[list[str], lambda a, b: (a + b)[-100:]]
    active_assignment: dict[str, Any] | None
    active_assignments: dict[str, dict[str, Any]]
    approval_request: dict[str, Any] | None
    validation_issues: list[dict[str, Any]]
    execution_results: list[dict[str, Any]]
    runtime_errors: list[dict[str, Any]]
    last_execution_status: str
    final_review: dict[str, Any] | None
    revision_tasks: list[dict[str, Any]]
    current_thread_id: Annotated[str, lambda a, b: b]
    contract_completed: bool
    plan_version: int
    blocked_reasons: Annotated[list[dict[str, Any]], lambda a, b: b]
    reservation_conflicts: list[dict[str, Any]]
    last_scope_change: dict[str, Any] | None
    last_heartbeat_at: str | None
    last_activity_at: str | None
    stalled_since: str | None
    reviewer_decision: str | None


def build_initial_state(
    *,
    project_name: str,
    task_description: str,
    project_id: str | None = None,
    current_thread_id: str,
) -> OrchestratorState:
    return {
        "project_id": project_id or str(uuid4()),
        "project_name": project_name,
        "task_description": task_description,
        "worker_queue": [],
        "dependencies": {},
        "file_registry": {},
        "worker_status": {"worker_a": "idle", "worker_b": "idle", "worker_c": "idle"},
        "worker_outputs": {"worker_a": [], "worker_b": [], "worker_c": []},
        "worker_failure_log": {"worker_a": [], "worker_b": [], "worker_c": []},
        "current_sprint": 1,
        "sprint_type": "feature",
        "sprint_status": "planning",
        "review_cycles": 0,
        "awaiting_approval": False,
        "approval_type": "",
        "active_approval_id": None,
        "context_summary": "",
        "manager_reply": None,
        "draft_plan": None,
        "conversation_history": [],
        "planning_status": "idle",
        "execution_requested": False,
        "suppress_user_turn": False,
        "planning_thread_id": current_thread_id,
        "scope_changed": False,
        "errors": [],
        "messages": [],
        "active_assignment": None,
        "active_assignments": {},
        "approval_request": None,
        "validation_issues": [],
        "execution_results": [],
        "runtime_errors": [],
        "last_execution_status": "not_run",
        "final_review": None,
        "revision_tasks": [],
        "current_thread_id": current_thread_id,
        "contract_completed": False,
        "plan_version": 1,
        "blocked_reasons": [],
        "reservation_conflicts": [],
        "last_scope_change": None,
        "last_heartbeat_at": None,
        "last_activity_at": None,
        "stalled_since": None,
        "reviewer_decision": None,
    }
