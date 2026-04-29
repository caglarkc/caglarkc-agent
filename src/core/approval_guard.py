from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from src.core.contracts import ApprovalDecision, ApprovalRequest, is_stale_approval, utc_now


@dataclass(frozen=True)
class ApprovalConsumeResult:
    outcome: str
    reason: str
    approval_id: str


class ApprovalGuard:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._active_approvals: dict[str, ApprovalRequest] = {}
        self._idempotency_index: set[tuple[str, str]] = set()

    async def register_approval(self, approval_request: ApprovalRequest) -> None:
        async with self._lock:
            self._active_approvals[approval_request.approval_id] = approval_request

    async def consume_decision(self, approval_decision: ApprovalDecision) -> ApprovalConsumeResult:
        async with self._lock:
            request = self._active_approvals.get(approval_decision.approval_id)
            idempotency_pair = (approval_decision.approval_id, approval_decision.idempotency_key)
            if idempotency_pair in self._idempotency_index:
                return ApprovalConsumeResult(
                    outcome="no-op",
                    reason="duplicate_idempotency_key",
                    approval_id=approval_decision.approval_id,
                )

            if is_stale_approval(request, approval_decision):
                return ApprovalConsumeResult(
                    outcome="stale",
                    reason="approval_not_active_or_expired",
                    approval_id=approval_decision.approval_id,
                )

            next_status = approval_decision.decision
            updated_request = request.model_copy(update={"status": next_status})
            self._active_approvals[approval_decision.approval_id] = updated_request
            self._idempotency_index.add(idempotency_pair)
            return ApprovalConsumeResult(
                outcome="accepted" if next_status == "approved" else next_status,
                reason="decision_consumed",
                approval_id=approval_decision.approval_id,
            )

    async def expire_timeouts(self, *, now: datetime | None = None) -> list[str]:
        async with self._lock:
            current_time = now or utc_now()
            expired: list[str] = []
            for approval_id, request in list(self._active_approvals.items()):
                expires_at = datetime.fromisoformat(request.expires_at)
                if request.status == "pending" and expires_at <= current_time:
                    self._active_approvals[approval_id] = request.model_copy(update={"status": "expired"})
                    expired.append(approval_id)
            return expired

    async def get_approval(self, approval_id: str) -> ApprovalRequest | None:
        async with self._lock:
            request = self._active_approvals.get(approval_id)
            return request.model_copy(deep=True) if request is not None else None
