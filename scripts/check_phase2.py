from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import aiofiles.os

from src.core.contracts import ApprovalDecision, ApprovalRequest, new_event
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.graph.graph import build_thread_config, graph_runtime
from src.graph.nodes.dispatcher import dispatcher_node
from src.graph.state import build_initial_state


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


async def _run_approved_flow(checkpoint_path: Path, *, thread_id: str) -> tuple[dict, dict]:
    bus = EventBus()
    manager = GraphManager(event_bus=bus)
    await manager.start()

    async with graph_runtime(checkpoint_path) as graph:
        manager.attach_graph(graph)
        config = build_thread_config(thread_id)
        manager.register_thread(thread_id, config)
        initial_state = build_initial_state(
            project_name="phase2-project",
            task_description="Build a helper and an app entrypoint.",
            current_thread_id=thread_id,
        )
        paused = await graph.ainvoke(initial_state, config=config)
        approval_id = paused["active_approval_id"]
        await bus.emit(
            "plan.approved",
            new_event(
                "plan.approved",
                payload={"approval_id": approval_id, "decision": "approved"},
                project_id=paused["project_id"],
                thread_id=thread_id,
                sprint_id=f"sprint-{paused['current_sprint']}",
                correlation_id=paused["project_id"],
                idempotency_key=f"approve-{thread_id}",
            ).model_dump(),
        )
        final_state = await graph.aget_state(config)
        return paused, final_state.values


async def check_basic_flow() -> CheckResult:
    checkpoint_path = Path("data/check_phase2_basic.sqlite")
    paused, final_state = await _run_approved_flow(checkpoint_path, thread_id=f"phase2-basic-{uuid4()}")
    expected_messages = {
        "planner completed",
        "dispatcher assigned helpers.py to worker_a",
        "worker completed helpers.py",
        "validator completed",
        "reviewer approved sprint",
    }
    if paused.get("awaiting_approval") is not True:
        return CheckResult("Basic Flow", False, "Planner approval pause olusmadi.")
    if final_state.get("sprint_status") != "approved":
        return CheckResult("Basic Flow", False, f"Final sprint_status approved degil: {final_state.get('sprint_status')}")
    if not expected_messages.issubset(set(final_state.get("messages", []))):
        return CheckResult("Basic Flow", False, f"Beklenen node zinciri mesajlari eksik: {final_state.get('messages')}")
    return CheckResult("Basic Flow", True, "planner->dispatcher->worker->validator->reviewer akis tamamlandi.")


async def check_dependency_order() -> CheckResult:
    state = build_initial_state(
        project_name="dep-order",
        task_description="dependency order",
        current_thread_id="dependency-thread",
    )
    state.update(
        {
            "dependencies": {"helpers.py": [], "app.py": ["helpers.py"]},
            "file_registry": {"helpers.py": "planned", "app.py": "planned"},
            "worker_queue": [
                {
                    "assignment": {
                        "task_id": "task-helpers",
                        "project_id": state["project_id"],
                        "thread_id": state["current_thread_id"],
                        "worker_id": "",
                        "target_file": "helpers.py",
                        "description": "helper",
                        "sprint_id": "sprint-1",
                        "correlation_id": state["project_id"],
                        "metadata": {},
                    },
                    "status": "planned",
                    "validation_error": None,
                },
                {
                    "assignment": {
                        "task_id": "task-app",
                        "project_id": state["project_id"],
                        "thread_id": state["current_thread_id"],
                        "worker_id": "",
                        "target_file": "app.py",
                        "description": "app",
                        "sprint_id": "sprint-1",
                        "correlation_id": state["project_id"],
                        "metadata": {},
                    },
                    "status": "planned",
                    "validation_error": None,
                },
            ],
        }
    )
    dispatched = await dispatcher_node(state)
    target = dispatched.get("active_assignment", {}).get("target_file")
    if target == "helpers.py":
        return CheckResult("Dependency Order", True, "Bagimli is, bagimlilik bitmeden secilmedi.")
    return CheckResult("Dependency Order", False, f"Yanlis atama yapildi: {target}")


async def check_stale_approval_no_resume() -> CheckResult:
    bus = EventBus()
    actions: list[str] = []

    async def on_resume(decision: ApprovalDecision) -> None:
        actions.append(decision.approval_id)

    manager = GraphManager(event_bus=bus, resume_callback=on_resume)
    await manager.start()
    await bus.emit(
        "plan.approved",
        new_event(
            "plan.approved",
            payload={"approval_id": "missing", "decision": "approved"},
            project_id="project-stale",
            thread_id="thread-stale",
            sprint_id="sprint-1",
            idempotency_key="stale-1",
        ).model_dump(),
    )
    if not actions:
        return CheckResult("Stale Approval", True, "Stale approval graph resume tetiklemedi.")
    return CheckResult("Stale Approval", False, f"Stale approval resume tetikledi: {actions}")


async def check_duplicate_approval_noop() -> CheckResult:
    bus = EventBus()
    actions: list[str] = []

    async def on_resume(decision: ApprovalDecision) -> None:
        actions.append(decision.approval_id)

    manager = GraphManager(event_bus=bus, resume_callback=on_resume)
    await manager.start()
    request = ApprovalRequest(
        approval_id="approval-dup",
        project_id="project-dup",
        thread_id="thread-dup",
        sprint_id="sprint-1",
        approval_type="plan",
    )
    await manager.register_approval(request)
    event = new_event(
        "plan.approved",
        payload={"approval_id": "approval-dup", "decision": "approved"},
        project_id="project-dup",
        thread_id="thread-dup",
        sprint_id="sprint-1",
        idempotency_key="dup-key",
    ).model_dump()
    first = await manager.on_plan_approved(event)
    second = await manager.on_plan_approved({**event, "event_id": str(uuid4())})
    if first.outcome == "accepted" and second.outcome == "no-op" and actions == ["approval-dup"]:
        return CheckResult("Duplicate Approval", True, "Duplicate idempotency approval no-op olarak kaldı.")
    return CheckResult("Duplicate Approval", False, f"Beklenmeyen duplicate sonucu: first={first}, second={second}, actions={actions}")


async def check_checkpoint_resume() -> CheckResult:
    checkpoint_path = Path("data/check_phase2_resume.sqlite")
    thread_id = f"phase2-resume-{uuid4()}"
    bus = EventBus()
    manager = GraphManager(event_bus=bus)
    await manager.start()

    async with graph_runtime(checkpoint_path) as graph:
        manager.attach_graph(graph)
        config = build_thread_config(thread_id)
        manager.register_thread(thread_id, config)
        initial_state = build_initial_state(
            project_name="resume-project",
            task_description="Resume from checkpoint after approval.",
            current_thread_id=thread_id,
        )
        paused = await graph.ainvoke(initial_state, config=config)
        if paused.get("awaiting_approval") is not True:
            return CheckResult("Checkpoint Resume", False, "Pause aninda awaiting_approval True degildi.")

    async with graph_runtime(checkpoint_path) as graph:
        manager.attach_graph(graph)
        config = build_thread_config(thread_id)
        manager.register_thread(thread_id, config)
        snapshot_before = await graph.aget_state(config)
        approval_id = snapshot_before.values["active_approval_id"]
        await bus.emit(
            "plan.approved",
            new_event(
                "plan.approved",
                payload={"approval_id": approval_id, "decision": "approved"},
                project_id=snapshot_before.values["project_id"],
                thread_id=thread_id,
                sprint_id=f"sprint-{snapshot_before.values['current_sprint']}",
                correlation_id=snapshot_before.values["project_id"],
                idempotency_key=f"resume-{thread_id}",
            ).model_dump(),
        )
        snapshot_after = await graph.aget_state(config)
        if snapshot_after.values.get("sprint_status") == "approved":
            return CheckResult("Checkpoint Resume", True, "Checkpoint write/read ve resume smoke gecti.")
        return CheckResult("Checkpoint Resume", False, f"Resume sonrasi sprint_status approved degil: {snapshot_after.values.get('sprint_status')}")


async def run_checks() -> list[CheckResult]:
    await aiofiles.os.makedirs("data", exist_ok=True)
    return [
        await check_basic_flow(),
        await check_dependency_order(),
        await check_stale_approval_no_resume(),
        await check_duplicate_approval_noop(),
        await check_checkpoint_resume(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    print("\n=== PHASE 2 ACCEPTANCE SUMMARY ===")
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
    print(f"PHASE_2_STATUS: {'READY' if fail_count == 0 else 'NOT_READY'}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
