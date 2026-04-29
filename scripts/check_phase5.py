from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from src.core.approval_guard import ApprovalGuard
from src.core.contracts import ApprovalRequest, new_event, utc_now
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.state_manager import StateManager
from src.interfaces.cli.app import OrchestratorCLIApp
from src.interfaces.cli.commands import CommandContext, execute_command
from src.interfaces.cli.notifier import CLINotifier


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


async def check_app_bootstrap() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    state_manager = StateManager()
    project_state = {
        "project_id": "project-bootstrap",
        "project_name": "bootstrap-project",
        "current_sprint": 1,
        "sprint_status": "planning",
        "sprint_type": "contract",
        "file_registry": {"api_contract.json": "planned"},
    }
    await state_manager.set("project-bootstrap", project_state)
    app = OrchestratorCLIApp(event_bus=bus, state_manager=state_manager)
    async with app.run_test() as pilot:
        await pilot.pause()
        sprint_panel = app.query_one("#sprint-panel")
        event_log = app.query_one("#event-log")
        approval_panel = app.query_one("#approval-panel")
        command_input = app.query_one("#command-input")
        if sprint_panel and event_log and approval_panel and command_input:
            return CheckResult("App Bootstrap", True, "Textual app bootstrap oldu ve paneller render edildi.")
    return CheckResult("App Bootstrap", False, "CLI app panelleri bootstrap edemedi.")


async def check_eventbus_ui_sync() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    state_manager = StateManager()
    app = OrchestratorCLIApp(event_bus=bus, state_manager=state_manager)
    async with app.run_test() as pilot:
        await pilot.pause()
        await bus.emit(
            "plan.approval_needed",
            new_event(
                "plan.approval_needed",
                payload={
                    "approval_id": "approval-ui",
                    "project_id": "project-ui",
                    "thread_id": "thread-ui",
                    "approval_type": "plan",
                    "requested_at": utc_now().isoformat(),
                    "expires_at": (utc_now() + timedelta(minutes=15)).isoformat(),
                    "status": "pending",
                },
                project_id="project-ui",
                thread_id="thread-ui",
                sprint_id="sprint-1",
                idempotency_key="approval-ui",
            ).model_dump(),
        )
        await bus.emit(
            "system.heartbeat",
            new_event(
                "system.heartbeat",
                payload={"task_id": "t1", "worker_id": "worker_a", "target_file": "helpers.py"},
                project_id="project-ui",
                thread_id="thread-ui",
                sprint_id="sprint-1",
            ).model_dump(),
        )
        await pilot.pause()
        if app.active_approval and app.current_state and app.current_state.get("last_heartbeat_at"):
            return CheckResult("EventBus UI Sync", True, "EventBus eventleri CLI state'ine dustu.")
    return CheckResult("EventBus UI Sync", False, "CLI EventBus eventlerini yansitamadi.")


async def check_task_publish() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    notifier = CLINotifier()
    context = CommandContext(
        event_bus=bus,
        graph_manager=None,
        notifier=notifier,
        state_manager=StateManager(),
        current_state={"project_id": "project-task", "current_thread_id": "thread-task"},
        active_approval=None,
    )
    outcome = await execute_command("/task implement dashboard", context)
    events = await bus.get_recent_events()
    if outcome.ok and events and events[-1]["event_name"] == "task.received":
        return CheckResult("Task Command", True, "/task komutu task.received publish etti.")
    return CheckResult("Task Command", False, f"/task publish basarisiz: outcome={outcome}, events={events}")


async def check_approve_active_approval() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    graph_manager = GraphManager(event_bus=bus)
    await graph_manager.start()
    request = ApprovalRequest(
        approval_id="approval-cli",
        project_id="project-cli",
        thread_id="thread-cli",
        sprint_id="sprint-1",
        approval_type="plan",
    )
    await graph_manager.register_approval(request)
    context = CommandContext(
        event_bus=bus,
        graph_manager=graph_manager,
        notifier=CLINotifier(),
        state_manager=StateManager(),
        current_state={"project_id": "project-cli", "current_thread_id": "thread-cli"},
        active_approval=request.model_dump(),
    )
    outcome = await execute_command("/approve", context)
    events = await bus.get_recent_events()
    if outcome.ok and any(item["event_name"] == "plan.approved" for item in events):
        return CheckResult("Approve Command", True, "/approve aktif approval ile dogru event gonderdi.")
    return CheckResult("Approve Command", False, f"/approve event gonderemedi: outcome={outcome}, events={events}")


async def check_stale_approval_safe() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    graph_manager = GraphManager(event_bus=bus, approval_guard=ApprovalGuard())
    await graph_manager.start()
    expired_request = ApprovalRequest(
        approval_id="approval-stale-cli",
        project_id="project-stale-cli",
        thread_id="thread-stale-cli",
        sprint_id="sprint-1",
        approval_type="plan",
        expires_at=(utc_now() - timedelta(minutes=1)).isoformat(),
    )
    await graph_manager.register_approval(expired_request)
    context = CommandContext(
        event_bus=bus,
        graph_manager=graph_manager,
        notifier=CLINotifier(),
        state_manager=StateManager(),
        current_state={"project_id": "project-stale-cli", "current_thread_id": "thread-stale-cli"},
        active_approval=expired_request.model_dump(),
    )
    outcome = await execute_command("/approve", context)
    events = await bus.get_recent_events()
    if not outcome.ok and not events:
        return CheckResult("Stale Approval", True, "Timeout olmus approval CLI tarafinda state degistirmeden reddedildi.")
    return CheckResult("Stale Approval", False, f"Stale approval guvenli degildi: outcome={outcome}, events={events}")


async def check_status_summary() -> CheckResult:
    context = CommandContext(
        event_bus=EventBus(),
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=StateManager(),
        current_state={
            "project_name": "status-project",
            "current_sprint": 2,
            "sprint_type": "feature",
            "sprint_status": "revision",
            "worker_queue": [1, 2],
            "worker_status": {"worker_a": "idle", "worker_b": "working"},
            "last_heartbeat_at": utc_now().isoformat(),
            "stalled_since": None,
            "active_assignment": None,
        },
        active_approval={"approval_id": "approval-status", "approval_type": "plan", "status": "pending"},
    )
    outcome = await execute_command("/status", context)
    if outcome.ok and "Project: status-project" in outcome.message and "Workers:" in outcome.message:
        return CheckResult("Status Command", True, "/status deterministic ve okunabilir ozet uretti.")
    return CheckResult("Status Command", False, f"/status beklenen ozeti uretmedi: {outcome.message}")


async def check_heartbeat_stalled_view() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    app = OrchestratorCLIApp(event_bus=bus, state_manager=StateManager())
    async with app.run_test() as pilot:
        await pilot.pause()
        heartbeat = new_event(
            "system.heartbeat",
            payload={"task_id": "hb", "worker_id": "worker_a", "target_file": "file.py"},
            project_id="project-hb",
            thread_id="thread-hb",
            sprint_id="sprint-1",
        ).model_dump()
        stalled = new_event(
            "system.stalled",
            payload={"reason": "silence"},
            project_id="project-hb",
            thread_id="thread-hb",
            sprint_id="sprint-1",
        ).model_dump()
        await bus.emit("system.heartbeat", heartbeat)
        await bus.emit("system.stalled", stalled)
        await pilot.pause()
        status = app.current_state or {}
        if status.get("last_heartbeat_at") and status.get("stalled_since"):
            return CheckResult("Heartbeat/Stalled View", True, "Heartbeat ve stalled bilgisi CLI state'inde gorunuyor.")
    return CheckResult("Heartbeat/Stalled View", False, "CLI heartbeat/stalled bilgisini gostermedi.")


async def run_checks() -> list[CheckResult]:
    return [
        await check_app_bootstrap(),
        await check_eventbus_ui_sync(),
        await check_task_publish(),
        await check_approve_active_approval(),
        await check_stale_approval_safe(),
        await check_status_summary(),
        await check_heartbeat_stalled_view(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    print("\n=== PHASE 5 ACCEPTANCE SUMMARY ===")
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
    print(f"PHASE_5_STATUS: {'READY' if fail_count == 0 else 'NOT_READY'}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
