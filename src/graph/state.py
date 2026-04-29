from __future__ import annotations

from typing import Any, TypedDict


class OrchestratorState(TypedDict, total=False):
    project_id: str
    project_name: str
    task_description: str
    file_registry: dict[str, str]
    dependencies: dict[str, list[str]]
    worker_queue: list[dict[str, Any]]
    worker_status: dict[str, str]
    worker_outputs: dict[str, list[str]]
    worker_failure_log: dict[str, list[str]]
    current_sprint: int
    sprint_type: str
    sprint_status: str
    review_cycles: int
    awaiting_approval: bool
    approval_type: str
    scope_changed: bool
    context_summary: str
    errors: list[dict[str, Any]]
    messages: list[str]
