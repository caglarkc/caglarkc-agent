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
    created_at: str = Field(default_factory=utc_now)
