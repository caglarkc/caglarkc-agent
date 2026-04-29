from __future__ import annotations

from typing import Any, Literal, TypedDict
from uuid import uuid4


FileStatus = Literal["planned", "reserved", "in_progress", "done", "failed"]


class QueueEntry(TypedDict, total=False):
    assignment: dict[str, Any]
    status: str
    validation_error: str | None


class OrchestratorState(TypedDict, total=False):
    project_id: str
    project_name: str
    task_description: str
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
    scope_changed: bool
    errors: list[dict[str, Any]]
    messages: list[str]
    active_assignment: dict[str, Any] | None
    approval_request: dict[str, Any] | None
    validation_issues: list[dict[str, Any]]
    revision_tasks: list[dict[str, Any]]
    current_thread_id: str


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
        "worker_status": {"worker_a": "idle"},
        "worker_outputs": {"worker_a": []},
        "worker_failure_log": {"worker_a": []},
        "current_sprint": 1,
        "sprint_type": "feature",
        "sprint_status": "planning",
        "review_cycles": 0,
        "awaiting_approval": False,
        "approval_type": "",
        "active_approval_id": None,
        "context_summary": "",
        "scope_changed": False,
        "errors": [],
        "messages": [],
        "active_assignment": None,
        "approval_request": None,
        "validation_issues": [],
        "revision_tasks": [],
        "current_thread_id": current_thread_id,
    }
