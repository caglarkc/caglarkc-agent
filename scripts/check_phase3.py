from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import aiofiles.os
import aiofiles.ospath

from src.core.context_builder import ContextBuilder
from src.core.event_bus import EventBus
from src.graph.nodes.dispatcher import dispatcher_node
from src.graph.nodes.planner import planner_node
from src.graph.nodes.reviewer import reviewer_node
from src.graph.nodes.worker import worker_node
from src.graph.state import build_initial_state
from src.storage.models import FileRecord
from src.storage.repository import Repository


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def merge_state(base: dict, updates: dict) -> dict:
    merged = dict(base)
    merged.update(updates)
    return merged


async def check_contract_sprint_gating() -> CheckResult:
    project_name = f"phase3-contract-{uuid4().hex[:8]}"
    state = build_initial_state(
        project_name=project_name,
        task_description="Build a new service.",
        current_thread_id=f"thread-{uuid4()}",
    )
    state["requested_sprint_type"] = "feature"
    plan = await planner_node(state)
    files = set(plan["file_registry"].keys())
    snapshot = Path("projects") / project_name / ".meta" / "sprints" / "sprint_001_v1.json"
    if plan["sprint_type"] != "contract":
        return CheckResult("Contract Sprint", False, f"Ilk sprint contract olmadi: {plan['sprint_type']}")
    if {"api_contract.json", "shared_types.py"}.difference(files):
        return CheckResult("Contract Sprint", False, f"Contract dosyalari eksik: {files}")
    if not await aiofiles.ospath.exists(snapshot):
        return CheckResult("Contract Sprint", False, f"Meta sprint snapshot yazilmadi: {snapshot}")

    state = merge_state(state, plan)
    state["awaiting_approval"] = False
    state["contract_completed"] = True
    state["current_sprint"] = 2
    state["requested_sprint_type"] = "feature"
    next_plan = await planner_node(state)
    next_files = set(next_plan["file_registry"].keys())
    if next_plan["sprint_type"] != "feature":
        return CheckResult("Contract Sprint", False, f"Contract sonrasi feature sprint baslamadi: {next_plan['sprint_type']}")
    if "api_contract.json" in next_files:
        return CheckResult("Contract Sprint", False, "Feature sprint contract dosyalarini yeniden urettti.")
    return CheckResult("Contract Sprint", True, "Contract sprint gating enforce edildi ve feature sprint erken baslamadi.")


async def check_file_reservation_conflict() -> CheckResult:
    repository = Repository()
    await repository.initialize()
    state = build_initial_state(
        project_name=f"phase3-reservation-{uuid4().hex[:8]}",
        task_description="Reservation conflict test.",
        current_thread_id=f"thread-{uuid4()}",
    )
    project_id = state["project_id"]
    await repository.upsert_file_record(
        FileRecord(
            file_id=str(uuid4()),
            project_id=project_id,
            sprint_id="sprint-1",
            path="shared_types.py",
            status="reserved",
            worker_id="worker_a",
            reservation_owner="worker_a",
        )
    )
    state.update(
        {
            "file_registry": {"shared_types.py": "reserved"},
            "active_assignment": {
                "task_id": "task-conflict",
                "project_id": project_id,
                "thread_id": state["current_thread_id"],
                "worker_id": "worker_b",
                "target_file": "shared_types.py",
                "description": "conflicting write",
                "sprint_id": "sprint-1",
                "correlation_id": project_id,
                "metadata": {"task_type": "contract_shared_types"},
            },
            "worker_queue": [
                {
                    "assignment": {
                        "task_id": "task-conflict",
                        "project_id": project_id,
                        "thread_id": state["current_thread_id"],
                        "worker_id": "worker_b",
                        "target_file": "shared_types.py",
                        "description": "conflicting write",
                        "sprint_id": "sprint-1",
                        "correlation_id": project_id,
                        "metadata": {"task_type": "contract_shared_types"},
                    },
                    "status": "assigned",
                    "retry_count": 0,
                    "blocked_by": [],
                    "task_type": "contract_shared_types",
                }
            ],
        }
    )
    result = await worker_node(state)
    if result.get("reservation_conflicts") and any(error["type"] == "reservation_conflict" for error in result.get("errors", [])):
        return CheckResult("File Reservation", True, "Reserved dosya ikinci worker tarafindan yazilamadi.")
    return CheckResult("File Reservation", False, f"Reservation conflict engellenmedi: {result}")


async def check_dependency_and_cycle_handling() -> CheckResult:
    state = build_initial_state(
        project_name=f"phase3-deps-{uuid4().hex[:8]}",
        task_description="Dependency ordering test.",
        current_thread_id=f"thread-{uuid4()}",
    )
    plan = await planner_node(state)
    state = merge_state(state, plan)
    state["awaiting_approval"] = False
    dispatch = await dispatcher_node(state)
    first_target = dispatch.get("active_assignment", {}).get("target_file")
    if first_target != "api_contract.json":
        return CheckResult("Dependency + Cycle", False, f"Ilk hazir is bagimsiz dosya olmadi: {first_target}")

    cycle_state = build_initial_state(
        project_name=f"phase3-cycle-{uuid4().hex[:8]}",
        task_description="Cycle detection test.",
        current_thread_id=f"thread-{uuid4()}",
    )
    cycle_state.update(
        {
            "dependencies": {"a.py": ["b.py"], "b.py": ["a.py"]},
            "file_registry": {"a.py": "planned", "b.py": "planned"},
            "worker_queue": [
                {
                    "assignment": {
                        "task_id": "a",
                        "project_id": cycle_state["project_id"],
                        "thread_id": cycle_state["current_thread_id"],
                        "worker_id": "unassigned",
                        "target_file": "a.py",
                        "description": "A",
                        "sprint_id": "sprint-1",
                        "correlation_id": cycle_state["project_id"],
                        "metadata": {"task_type": "cycle_a"},
                    },
                    "status": "planned",
                    "retry_count": 0,
                    "blocked_by": [],
                    "task_type": "cycle_a",
                }
            ],
        }
    )
    cycle_dispatch = await dispatcher_node(cycle_state)
    if cycle_dispatch.get("sprint_status") == "fail":
        return CheckResult("Dependency + Cycle", True, "Dependency ordering korundu ve cycle sprint fail olarak yakalandi.")
    return CheckResult("Dependency + Cycle", False, f"Cycle handling fail vermedi: {cycle_dispatch}")


async def check_retry_and_worker_failed() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    failed_events: list[dict] = []

    async def on_failed(payload: dict) -> None:
        failed_events.append(payload)

    await bus.subscribe("worker.failed", on_failed)

    state = build_initial_state(
        project_name=f"phase3-retry-{uuid4().hex[:8]}",
        task_description="Retry behavior test.",
        current_thread_id=f"thread-{uuid4()}",
    )
    project_id = state["project_id"]
    state.update(
        {
            "file_registry": {"fragile.py": "planned"},
            "dependencies": {"fragile.py": []},
            "worker_queue": [
                {
                    "assignment": {
                        "task_id": "fragile-task",
                        "project_id": project_id,
                        "thread_id": state["current_thread_id"],
                        "worker_id": "unassigned",
                        "target_file": "fragile.py",
                        "description": "fragile task",
                        "sprint_id": "sprint-1",
                        "correlation_id": project_id,
                        "metadata": {"task_type": "fragile_task", "simulate_error": "retryable"},
                    },
                    "status": "planned",
                    "retry_count": 0,
                    "blocked_by": [],
                    "task_type": "fragile_task",
                }
            ],
        }
    )

    for _ in range(3):
        dispatched = await dispatcher_node(state)
        state = merge_state(state, dispatched)
        worked = await worker_node(state)
        state = merge_state(state, worked)

    repository = Repository()
    failures = await repository.list_worker_failures(project_id, limit=10)
    queue_entry = state["worker_queue"][0]
    if state.get("file_registry", {}).get("fragile.py") != "failed":
        return CheckResult("Retry + Failure", False, f"3 retry sonunda dosya failed olmadi: {state['file_registry']}")
    if queue_entry.get("retry_count") != 3 or queue_entry.get("status") != "failed":
        return CheckResult("Retry + Failure", False, f"Retry sayaci/status beklenen degil: {queue_entry}")
    if len(failed_events) != 1 or len(failures) < 3:
        return CheckResult("Retry + Failure", False, f"worker.failed veya repository kaydi eksik: events={len(failed_events)}, failures={len(failures)}")
    return CheckResult("Retry + Failure", True, "Retry politikasi 3 deneme sonunda worker.failed ve kalici failure kaydi uretti.")


async def check_failure_learning_context() -> CheckResult:
    project_name = f"phase3-learning-{uuid4().hex[:8]}"
    state = build_initial_state(
        project_name=project_name,
        task_description="Failure learning test.",
        current_thread_id=f"thread-{uuid4()}",
    )
    project_id = state["project_id"]
    state.update(
        {
            "file_registry": {"fragile.py": "planned"},
            "dependencies": {"fragile.py": []},
            "worker_queue": [
                {
                    "assignment": {
                        "task_id": "fragile-task",
                        "project_id": project_id,
                        "thread_id": state["current_thread_id"],
                        "worker_id": "unassigned",
                        "target_file": "fragile.py",
                        "description": "fragile task",
                        "sprint_id": "sprint-1",
                        "correlation_id": project_id,
                        "metadata": {"task_type": "fragile_task", "simulate_error": "retryable"},
                    },
                    "status": "planned",
                    "retry_count": 0,
                    "blocked_by": [],
                    "task_type": "fragile_task",
                }
            ],
        }
    )
    for _ in range(2):
        state = merge_state(state, await dispatcher_node(state))
        state = merge_state(state, await worker_node(state))

    summary = await ContextBuilder().build(project_id, project_name)
    if "Failure Learning:" in summary and "reassign" in summary:
        return CheckResult("Failure Learning", True, "Failure pattern sonraki sprint context'ine inject edildi.")
    return CheckResult("Failure Learning", False, f"Failure learning context'e yansimadi: {summary}")


async def check_scope_change_replan() -> CheckResult:
    project_name = f"phase3-scope-{uuid4().hex[:8]}"
    state = build_initial_state(
        project_name=project_name,
        task_description="Scope change test.",
        current_thread_id=f"thread-{uuid4()}",
    )
    plan = await planner_node(state)
    state = merge_state(state, plan)
    state["awaiting_approval"] = False
    dispatched = await dispatcher_node(state)
    state = merge_state(state, dispatched)
    state["scope_changed"] = True
    state["scope_change_reason"] = "new requirement during sprint"
    paused = await dispatcher_node(state)
    state = merge_state(state, paused)
    replanned = await planner_node(state)
    if paused.get("active_assignment") is not None:
        return CheckResult("Scope Change", False, "Scope change sirasinda active assignment temizlenmedi.")
    if replanned.get("plan_version", 1) <= plan.get("plan_version", 1):
        return CheckResult("Scope Change", False, f"Replan version artmadi: before={plan.get('plan_version')}, after={replanned.get('plan_version')}")
    if replanned.get("scope_changed") is not False:
        return CheckResult("Scope Change", False, "Replan sonrasi scope_changed temizlenmedi.")
    return CheckResult("Scope Change", True, "Scope change aktif isi guvenli durdurup DAG'i yeniden planladi.")


async def run_checks() -> list[CheckResult]:
    await aiofiles.os.makedirs("data", exist_ok=True)
    return [
        await check_contract_sprint_gating(),
        await check_file_reservation_conflict(),
        await check_dependency_and_cycle_handling(),
        await check_retry_and_worker_failed(),
        await check_failure_learning_context(),
        await check_scope_change_replan(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    print("\n=== PHASE 3 ACCEPTANCE SUMMARY ===")
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
    print(f"PHASE_3_STATUS: {'READY' if fail_count == 0 else 'NOT_READY'}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
