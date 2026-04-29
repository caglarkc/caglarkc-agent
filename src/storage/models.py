from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Project(BaseModel):
    project_id: str
    name: str
    description: str
    status: str = "planning"
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Sprint(BaseModel):
    sprint_id: str
    project_id: str
    number: int
    sprint_type: str
    status: str = "planning"
    plan_version: int = 1
    review_cycles: int = 0
    files_written: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    revision_notes: list[str] = Field(default_factory=list)
    started_at: str = Field(default_factory=utc_now)
    completed_at: str | None = None


class FileRecord(BaseModel):
    file_id: str
    project_id: str
    sprint_id: str | None = None
    path: str
    status: str = "planned"
    worker_id: str | None = None
    checksum: str | None = None
    attempt_count: int = 0
    last_error: str | None = None
    reservation_owner: str | None = None
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class Decision(BaseModel):
    decision_id: str
    project_id: str
    sprint_id: str | None = None
    summary: str
    rationale: str = ""
    created_at: str = Field(default_factory=utc_now)


class WorkerFailureLog(BaseModel):
    failure_id: str
    project_id: str
    sprint_id: str | None = None
    worker_id: str
    task_type: str
    error_message: str
    retryable: bool = True
    retry_count: int = 1
    recommendation: str = ""
    created_at: str = Field(default_factory=utc_now)


class ProjectSummary(BaseModel):
    project_id: str
    project_name: str
    status: str
    total_sprints: int = 0
    total_files_written: int = 0
    total_duration_seconds: int = 0
    worker_success_rates: dict[str, float] = Field(default_factory=dict)
    retry_failure_rate: float = 0.0
    archived: bool = False
