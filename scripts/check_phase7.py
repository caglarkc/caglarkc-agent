from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import aiofiles.os

from main import OllamaGateResult, OrchestratorDaemon
from scripts.healthcheck import gather_health
from src.config.settings import get_settings
from src.core.approval_guard import ApprovalGuard
from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.state_manager import StateManager
from src.graph.graph import build_thread_config
from src.graph.state import build_initial_state
from src.storage.models import FileRecord, Project
from src.storage.repository import Repository


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


class FakeService:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    async def shutdown(self) -> None:
        self.stopped = True


def configure_test_environment() -> Path:
    base = Path("data") / f"phase7-check-{uuid4().hex[:8]}"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    os.environ["DATA_DIR"] = str(base)
    os.environ["PROJECTS_ROOT"] = str(base / "projects")
    os.environ["SQLITE_DB_PATH"] = str(base / "orchestrator.db")
    os.environ["GRAPH_CHECKPOINT_PATH"] = str(base / "checkpoints.sqlite")
    os.environ["TELEGRAM_BOT_TOKEN"] = "phase7-telegram-token"
    os.environ["TELEGRAM_CHAT_ID"] = "1001"
    os.environ["OLLAMA_MODEL"] = "qwen2.5:latest"
    get_settings.cache_clear()
    return base


async def reset_singletons() -> tuple[EventBus, StateManager]:
    bus = EventBus()
    await bus.reset()
    state_manager = StateManager()
    await state_manager.reset()
    return bus, state_manager


async def build_daemon(
    *,
    enable_cli: bool = False,
    enable_telegram: bool = True,
    ollama_probe=None,
) -> tuple[OrchestratorDaemon, FakeService, FakeService]:
    bus, state_manager = await reset_singletons()
    repository = Repository()
    graph_manager = GraphManager(
        event_bus=bus,
        state_manager=state_manager,
        repository=repository,
        approval_guard=ApprovalGuard(),
    )
    fake_bot = FakeService()
    fake_cli = FakeService()
    daemon = OrchestratorDaemon(
        enable_cli=enable_cli,
        enable_telegram=enable_telegram,
        event_bus=bus,
        state_manager=state_manager,
        repository=repository,
        graph_manager=graph_manager,
        telegram_bot=fake_bot,
        cli_service=fake_cli,
        ollama_probe=ollama_probe or (lambda: asyncio.sleep(0, result=OllamaGateResult("healthy", "ok", 1))),
    )
    return daemon, fake_bot, fake_cli


async def check_daemon_bootstrap() -> CheckResult:
    daemon, fake_bot, fake_cli = await build_daemon(enable_cli=True, enable_telegram=True)
    try:
        result = await daemon.start()
        status_path = get_settings().daemon_status_path
        if daemon.graph_manager.graph is None:
            return CheckResult("Daemon Bootstrap", False, "Graph runtime ayaga kalkmadi.")
        if not fake_bot.started or not fake_cli.started:
            return CheckResult("Daemon Bootstrap", False, "Interface servisleri baslamadi.")
        if status_path.exists() and result["ollama"]["status"] == "healthy":
            return CheckResult("Daemon Bootstrap", True, "Daemon bootstrap deterministic sirayla calisti.")
        return CheckResult("Daemon Bootstrap", False, f"Beklenen status dosyasi veya gate sonucu yok: {result}")
    finally:
        await daemon.shutdown("bootstrap_check_done")


async def check_graceful_shutdown() -> CheckResult:
    daemon, fake_bot, fake_cli = await build_daemon(enable_cli=True, enable_telegram=True)
    await daemon.start()
    await daemon.trigger_signal_shutdown("SIGTERM")
    pid_exists = get_settings().daemon_pid_path.exists()
    if daemon.shutdown_event.is_set() and fake_bot.stopped and fake_cli.stopped and not pid_exists:
        return CheckResult("Graceful Shutdown", True, "Signal ile kontrollu shutdown ve flush gerceklesti.")
    return CheckResult(
        "Graceful Shutdown",
        False,
        f"Shutdown eksik: event={daemon.shutdown_event.is_set()} bot={fake_bot.stopped} cli={fake_cli.stopped} pid={pid_exists}",
    )


async def check_ollama_health_gate() -> CheckResult:
    attempts = {"count": 0}

    async def flaky_probe() -> OllamaGateResult:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary_ollama_error")
        return OllamaGateResult("healthy", "model_ready:qwen2.5:latest", attempts["count"])

    daemon, _, _ = await build_daemon(ollama_probe=flaky_probe)
    try:
        result = await daemon.run_ollama_gate(max_attempts=3)
        if result.status == "healthy" and attempts["count"] == 3:
            return CheckResult("Ollama Gate", True, "Ollama gate retry/backoff ile sonunda saglikli gecti.")
        return CheckResult("Ollama Gate", False, f"Beklenen retry davranisi olmadi: {result} attempts={attempts['count']}")
    finally:
        await daemon.shutdown("ollama_gate_check_done")


async def _create_pending_thread(graph_manager: GraphManager) -> tuple[str, dict]:
    await graph_manager.start()
    await graph_manager.bootstrap_runtime()
    thread_id = f"thread-{uuid4()}"
    config = build_thread_config(thread_id)
    graph_manager.register_thread(thread_id, config)
    initial_state = build_initial_state(
        project_name=f"phase7-project-{uuid4().hex[:6]}",
        task_description="Crash recovery test",
        current_thread_id=thread_id,
    )
    await graph_manager.graph.ainvoke(initial_state, config=config)
    snapshot = await graph_manager.graph.aget_state(config)
    return thread_id, snapshot.values


async def check_crash_recovery_and_resume() -> CheckResult:
    await reset_singletons()
    first_manager = GraphManager(
        event_bus=EventBus(),
        state_manager=StateManager(),
        repository=Repository(),
        approval_guard=ApprovalGuard(),
    )
    thread_id, snapshot_values = await _create_pending_thread(first_manager)
    approval_request = snapshot_values.get("approval_request", {})
    await first_manager.shutdown_runtime()

    recovered_events: list[dict] = []
    bus = EventBus()
    await bus.reset()

    async def on_recovered(payload: dict) -> None:
        recovered_events.append(payload)

    await bus.subscribe("system.recovered", on_recovered)
    state_manager = StateManager()
    await state_manager.reset()
    second_manager = GraphManager(
        event_bus=bus,
        state_manager=state_manager,
        repository=Repository(),
        approval_guard=ApprovalGuard(),
    )
    await second_manager.start()
    await second_manager.bootstrap_runtime()
    recovery = await second_manager.recover_pending_threads()

    approval_event = new_event(
        "plan.approved",
        payload={
            "approval_id": approval_request["approval_id"],
            "decision": "approved",
            "reason": "resume_after_recovery",
        },
        project_id=snapshot_values["project_id"],
        thread_id=thread_id,
        sprint_id=f"sprint-{snapshot_values['current_sprint']}",
        idempotency_key=f"recover-{approval_request['approval_id']}",
    ).model_dump()
    await bus.emit("plan.approved", approval_event)
    config = build_thread_config(thread_id)
    refreshed = await second_manager.graph.aget_state(config)
    try:
        if not recovered_events:
            return CheckResult("Crash Recovery", False, "Recovery sonrasi system.recovered event'i emit edilmedi.")
        if not recovery["recovered_threads"]:
            return CheckResult("Crash Recovery", False, "Pending thread recovery listesine dusmedi.")
        if refreshed.values.get("awaiting_approval"):
            return CheckResult("Crash Recovery", False, "Recovery sonrasi approval bridge graph'i devam ettirmedi.")
        return CheckResult("Crash Recovery", True, "Crash recovery checkpoint'ten state okuyup guvenli resume etti.")
    finally:
        await second_manager.shutdown_runtime()


async def check_orphan_reserved_cleanup() -> CheckResult:
    bus, state_manager = await reset_singletons()
    repository = Repository()
    await repository.initialize()
    project = Project(project_id="project-orphan", name="orphan", description="orphan cleanup", status="active")
    await repository.upsert_project(project)
    await repository.upsert_file_record(
        FileRecord(
            file_id=str(uuid4()),
            project_id=project.project_id,
            sprint_id="sprint-1",
            path="stuck.py",
            status="reserved",
            worker_id="worker_a",
            reservation_owner="worker_a",
        )
    )
    await state_manager.set(project.project_id, {"project_id": project.project_id, "file_registry": {"stuck.py": "reserved"}})
    manager = GraphManager(event_bus=bus, state_manager=state_manager, repository=repository)
    cleaned = await manager.cleanup_orphan_reservations()
    record = await repository.get_file_record(project.project_id, "stuck.py")
    state = await state_manager.get(project.project_id)
    if cleaned == 1 and record is not None and record.status == "planned" and state["file_registry"]["stuck.py"] == "planned":
        return CheckResult("Orphan Cleanup", True, "Orphan reserved kayitlar reclaim edildi.")
    return CheckResult("Orphan Cleanup", False, f"Cleanup beklenen sonucu vermedi: cleaned={cleaned} record={record} state={state}")


async def check_replay_safe_resume() -> CheckResult:
    bus, state_manager = await reset_singletons()
    manager = GraphManager(
        event_bus=bus,
        state_manager=state_manager,
        repository=Repository(),
        approval_guard=ApprovalGuard(),
    )
    await manager.start()
    approval_request = {
        "approval_id": "approval-replay",
        "project_id": "project-replay",
        "thread_id": "thread-replay",
        "sprint_id": "sprint-1",
        "approval_type": "plan",
    }
    await manager.on_plan_approval_needed(
        new_event(
            "plan.approval_needed",
            payload=approval_request,
            project_id="project-replay",
            thread_id="thread-replay",
            sprint_id="sprint-1",
            idempotency_key="approval-replay",
        ).model_dump()
    )
    event = new_event(
        "plan.approved",
        payload={"approval_id": "approval-replay", "decision": "approved"},
        project_id="project-replay",
        thread_id="thread-replay",
        sprint_id="sprint-1",
        idempotency_key="dup-key",
        event_id="event-dup",
    ).model_dump()
    first = await manager._handle_decision_event(event, expected_event_type="plan.approved")
    second = await manager._handle_decision_event(event, expected_event_type="plan.approved")
    if first.outcome == "accepted" and second.outcome == "no-op":
        return CheckResult("Replay-safe Resume", True, "Duplicate event ikinci kez state degisikligi yaratmadi.")
    return CheckResult("Replay-safe Resume", False, f"Replay-safe davranis bozuk: first={first} second={second}")


async def check_healthcheck_output() -> CheckResult:
    daemon, _, _ = await build_daemon()
    try:
        await daemon.start()
        await daemon.event_bus.emit(
            "system.heartbeat",
            {"timestamp": "2026-04-30T12:00:00+00:00", "payload": {"worker_id": "worker_a"}},
        )
        health = await gather_health()
        expected_keys = {"PROCESS_ALIVE", "PID", "LAST_HEARTBEAT", "STALLED", "CHECKPOINT_ACCESS", "TELEGRAM", "OLLAMA"}
        if expected_keys.issubset(set(health)) and health["CHECKPOINT_ACCESS"]:
            return CheckResult("Healthcheck", True, "Healthcheck script okunabilir ve deterministik ozet uretti.")
        return CheckResult("Healthcheck", False, f"Healthcheck beklenen anahtarlari uretmedi: {health}")
    finally:
        await daemon.shutdown("healthcheck_done")


async def check_systemd_unit() -> CheckResult:
    service_path = Path("ai-orchestrator.service")
    content = service_path.read_text(encoding="utf-8")
    required = ["ExecStart=", "Restart=on-failure", "RestartSec=10", "WorkingDirectory=", "EnvironmentFile="]
    if all(token in content for token in required):
        return CheckResult("Systemd Unit", True, "Systemd unit dosyasi temel daemon ayarlarini tasiyor.")
    return CheckResult("Systemd Unit", False, "Systemd unit icinde zorunlu alanlar eksik.")


async def run_checks() -> list[CheckResult]:
    configure_test_environment()
    await aiofiles.os.makedirs(get_settings().data_dir, exist_ok=True)
    return [
        await check_daemon_bootstrap(),
        await check_graceful_shutdown(),
        await check_ollama_health_gate(),
        await check_crash_recovery_and_resume(),
        await check_orphan_reserved_cleanup(),
        await check_replay_safe_resume(),
        await check_healthcheck_output(),
        await check_systemd_unit(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    print("\n=== PHASE 7 ACCEPTANCE SUMMARY ===")
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
    print(f"PHASE_7_STATUS: {'READY' if fail_count == 0 else 'NOT_READY'}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
