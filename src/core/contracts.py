from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


DEFAULT_APPROVAL_TIMEOUT_MINUTES = 15
CONTRACT_VERSION = "v1"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ContractValidationError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field_name: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class EventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: str
    version: str = CONTRACT_VERSION
    timestamp: str = Field(default_factory=lambda: utc_now().isoformat())
    project_id: str | None = None
    thread_id: str | None = None
    sprint_id: str | None = None
    correlation_id: str | None = None
    idempotency_key: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id", "event_type", "version")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("value cannot be empty")
        return value.strip()

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        datetime.fromisoformat(value)
        return value


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    project_id: str
    thread_id: str
    approval_type: str
    requested_at: str = Field(default_factory=lambda: utc_now().isoformat())
    expires_at: str = Field(
        default_factory=lambda: (utc_now() + timedelta(minutes=DEFAULT_APPROVAL_TIMEOUT_MINUTES)).isoformat()
    )
    status: Literal["pending", "approved", "rejected", "cancelled", "expired"] = "pending"
    sprint_id: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("approval_id", "project_id", "thread_id", "approval_type")
    @classmethod
    def validate_required(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("value cannot be empty")
        return value.strip()

    @field_validator("requested_at", "expires_at")
    @classmethod
    def validate_datetime(cls, value: str) -> str:
        datetime.fromisoformat(value)
        return value


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    decision: Literal["approved", "rejected", "cancelled"]
    decided_at: str = Field(default_factory=lambda: utc_now().isoformat())
    idempotency_key: str
    project_id: str
    thread_id: str
    sprint_id: str | None = None
    reason: str | None = None

    @field_validator("approval_id", "idempotency_key", "project_id", "thread_id")
    @classmethod
    def validate_required(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("value cannot be empty")
        return value.strip()

    @field_validator("decided_at")
    @classmethod
    def validate_datetime(cls, value: str) -> str:
        datetime.fromisoformat(value)
        return value


class DispatchAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    project_id: str
    thread_id: str
    worker_id: str
    target_file: str
    description: str
    sprint_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("task_id", "project_id", "thread_id", "worker_id", "target_file", "description")
    @classmethod
    def validate_required(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("value cannot be empty")
        return value.strip()


def new_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    project_id: str | None = None,
    thread_id: str | None = None,
    sprint_id: str | None = None,
    correlation_id: str | None = None,
    idempotency_key: str | None = None,
    event_id: str | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id or str(uuid4()),
        event_type=event_type,
        version=CONTRACT_VERSION,
        timestamp=utc_now().isoformat(),
        project_id=project_id,
        thread_id=thread_id,
        sprint_id=sprint_id,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        payload=payload,
    )


def validate_event(raw_event: EventEnvelope | dict[str, Any]) -> EventEnvelope:
    if isinstance(raw_event, EventEnvelope):
        return raw_event
    return EventEnvelope.model_validate(raw_event)


def event_validation_error(exc: ValidationError) -> ContractValidationError:
    error = exc.errors()[0]
    location = error.get("loc", [])
    field_name = ".".join(str(item) for item in location) if location else None
    return ContractValidationError(
        code="contract_validation_error",
        message=error.get("msg", "invalid event payload"),
        field_name=field_name,
        details={"type": error.get("type", "unknown")},
    )


def is_stale_approval(
    approval_request: ApprovalRequest | None,
    approval_decision: ApprovalDecision,
    *,
    now: datetime | None = None,
) -> bool:
    if approval_request is None:
        return True
    current_time = now or utc_now()
    expires_at = datetime.fromisoformat(approval_request.expires_at)
    if approval_request.status != "pending":
        return True
    if expires_at <= current_time:
        return True
    if approval_request.approval_id != approval_decision.approval_id:
        return True
    if approval_request.project_id != approval_decision.project_id:
        return True
    if approval_request.thread_id != approval_decision.thread_id:
        return True
    if approval_request.sprint_id and approval_decision.sprint_id and approval_request.sprint_id != approval_decision.sprint_id:
        return True
    return False
