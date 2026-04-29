from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from src.core.approval_guard import ApprovalGuard
from src.core.contracts import ApprovalDecision, ApprovalRequest, is_stale_approval, new_event, validate_event, utc_now
from src.core.graph_manager import GraphManager
from src.core.retry_policy import RetryPolicy, classify_error
from src.core.state_transaction import StateTransaction
from src.core.state_manager import StateManager


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


class RateLimitError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"status={status_code}")
        self.status_code = status_code


class AuthError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"status={status_code}")
        self.status_code = status_code


async def check_contract_validation() -> CheckResult:
    event = new_event(
        "plan.approved",
        payload={"approval_id": "approval-1", "decision": "approved"},
        project_id="project-1",
        thread_id="thread-1",
        sprint_id="sprint-1",
        idempotency_key="idem-1",
    )
    validated = validate_event(event.model_dump())
    if validated.event_type != "plan.approved" or validated.version != "v1":
        return CheckResult("Contract Validation", False, "Event envelope validation sonucu beklenen degil.")

    try:
        validate_event({"event_type": "broken", "payload": {}})
    except Exception:
        return CheckResult("Contract Validation", True, "Gecerli event kabul edildi, bozuk payload reddedildi.")
    return CheckResult("Contract Validation", False, "Bozuk event payload reddedilmedi.")


async def check_stale_approval() -> CheckResult:
    guard = ApprovalGuard()
    request = ApprovalRequest(
        approval_id="approval-stale",
        project_id="project-1",
        thread_id="thread-1",
        sprint_id="sprint-1",
        approval_type="plan",
        expires_at=(utc_now() - timedelta(minutes=1)).isoformat(),
    )
    decision = ApprovalDecision(
        approval_id="approval-stale",
        decision="approved",
        idempotency_key="idem-stale",
        project_id="project-1",
        thread_id="thread-1",
        sprint_id="sprint-1",
    )
    await guard.register_approval(request)
    result = await guard.consume_decision(decision)
    if result.outcome == "stale" and is_stale_approval(request, decision):
        return CheckResult("Stale Approval", True, "Expired approval state degisikligi yaratmadan reddedildi.")
    return CheckResult("Stale Approval", False, f"Beklenen stale sonucu alinmadi: {result}")


async def check_idempotent_approval() -> CheckResult:
    guard = ApprovalGuard()
    request = ApprovalRequest(
        approval_id="approval-idem",
        project_id="project-2",
        thread_id="thread-2",
        sprint_id="sprint-2",
        approval_type="plan",
    )
    decision = ApprovalDecision(
        approval_id="approval-idem",
        decision="approved",
        idempotency_key="idem-repeat",
        project_id="project-2",
        thread_id="thread-2",
        sprint_id="sprint-2",
    )
    await guard.register_approval(request)
    first = await guard.consume_decision(decision)
    second = await guard.consume_decision(decision)
    if first.outcome == "accepted" and second.outcome == "stale":
        return CheckResult("Idempotent Approval", False, "Duplicate decision stale oldu, no-op bekleniyordu.")
    if first.outcome == "accepted" and second.outcome == "no-op":
        return CheckResult("Idempotent Approval", True, "Ayni idempotency key duplicate isleme yol acmadi.")
    return CheckResult("Idempotent Approval", False, f"Beklenmeyen sonuc: first={first}, second={second}")


async def check_retry_policy() -> CheckResult:
    retry_policy = RetryPolicy(seed=7)
    delays = [retry_policy.next_delay(1), retry_policy.next_delay(2), retry_policy.next_delay(3)]
    if not (delays[0] < delays[1] < delays[2]):
        return CheckResult("Retry Policy", False, f"Backoff siralamasi bozuk: {delays}")

    retryable = classify_error(asyncio.TimeoutError())
    rate_limited = classify_error(RateLimitError(429))
    non_retryable = classify_error(AuthError(401))
    if retryable.retryable and rate_limited.retryable and not non_retryable.retryable:
        return CheckResult("Retry Policy", True, f"Backoff ve siniflandirma gecerli: {delays}")
    return CheckResult("Retry Policy", False, "Retryable/non-retryable siniflandirma hatali.")


async def check_state_transaction_rollback() -> CheckResult:
    state_manager = StateManager()
    await state_manager.set("project-tx", {"status": "before", "count": 1})
    try:
        async with StateTransaction("project-tx", state_manager=state_manager) as transaction:
            state = transaction.state
            state["status"] = "mutated"
            state["count"] = 99
            transaction.state = state
            raise RuntimeError("rollback")
    except RuntimeError:
        pass

    rolled_back = await state_manager.get("project-tx")
    if rolled_back == {"status": "before", "count": 1}:
        return CheckResult("State Transaction", True, "Exception durumunda rollback calisti.")
    return CheckResult("State Transaction", False, f"Rollback basarisiz: {rolled_back}")


async def check_graph_manager_bridge() -> CheckResult:
    state_manager = StateManager()
    await state_manager.delete("project-bridge")
    actions: list[str] = []

    async def on_resume(decision: ApprovalDecision) -> None:
        actions.append(f"resume:{decision.approval_id}")

    manager = GraphManager(resume_callback=on_resume)
    request = ApprovalRequest(
        approval_id="approval-bridge",
        project_id="project-bridge",
        thread_id="thread-bridge",
        sprint_id="sprint-bridge",
        approval_type="plan",
    )
    await manager.register_approval(request)
    accepted_event = new_event(
        "plan.approved",
        payload={"approval_id": "approval-bridge", "decision": "approved"},
        project_id="project-bridge",
        thread_id="thread-bridge",
        sprint_id="sprint-bridge",
        idempotency_key="bridge-1",
    )
    duplicate_event = accepted_event.model_copy(update={"event_id": "event-duplicate"})
    stale_event = new_event(
        "plan.approved",
        payload={"approval_id": "approval-missing", "decision": "approved"},
        project_id="project-bridge",
        thread_id="thread-bridge",
        sprint_id="sprint-bridge",
        idempotency_key="bridge-2",
    )

    first = await manager.on_plan_approved(accepted_event.model_dump())
    second = await manager.on_plan_approved(duplicate_event.model_dump())
    third = await manager.on_plan_approved(stale_event.model_dump())
    project_state = await state_manager.get("project-bridge")

    if first.outcome != "accepted":
        return CheckResult("GraphManager Bridge", False, f"Ilk karar kabul edilmedi: {first}")
    if second.outcome != "no-op":
        return CheckResult("GraphManager Bridge", False, f"Duplicate karar no-op olmadi: {second}")
    if third.outcome != "stale":
        return CheckResult("GraphManager Bridge", False, f"Stale karar stale olmadi: {third}")
    if actions != ["resume:approval-bridge"]:
        return CheckResult("GraphManager Bridge", False, f"Resume duplicate/stale icin tetiklendi: {actions}")
    if project_state["approvals"]["approval-bridge"]["decision"] != "approved":
        return CheckResult("GraphManager Bridge", False, f"State bridge guncellenemedi: {project_state}")
    return CheckResult("GraphManager Bridge", True, "Accepted/no-op/stale kararlar bridge seviyesinde dogru ayrildi.")


async def run_checks() -> list[CheckResult]:
    return [
        await check_contract_validation(),
        await check_stale_approval(),
        await check_idempotent_approval(),
        await check_retry_policy(),
        await check_state_transaction_rollback(),
        await check_graph_manager_bridge(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    phase_status = "READY" if fail_count == 0 else "NOT_READY"

    print("\n=== PHASE 1.5 ACCEPTANCE SUMMARY ===")
    print(f"TOTAL_CHECKS: {len(results)}")
    print(f"PASS: {pass_count}")
    print(f"FAIL: {fail_count}")
    if fail_count:
        print("FAIL_REASONS:")
        for item in results:
            if not item.passed:
                print(f"- {item.name}: {item.detail}")
    else:
        print("FAIL_REASONS: none")
    print(f"PHASE_1_5_STATUS: {phase_status}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
