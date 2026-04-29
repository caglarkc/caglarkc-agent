from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from src.config.settings import get_settings
from src.core.approval_guard import ApprovalGuard
from src.core.contracts import ApprovalRequest, new_event
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.project_manager import ProjectManager
from src.core.scheduler import FairScheduler, ScheduledTask
from src.core.state_manager import StateManager
from src.interfaces.cli.commands import CommandContext, execute_command
from src.interfaces.cli.notifier import CLINotifier
from src.interfaces.telegram.handlers import TelegramHandlerContext, handle_history, handle_projects
from src.storage.models import FileRecord, Project, Sprint, WorkerFailureLog, utc_now
from src.storage.repository import Repository


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


class FakeChat:
    def __init__(self, chat_id: int) -> None:
        self.id = chat_id


class FakeMessage:
    def __init__(self, chat_id: int, text: str = "") -> None:
        self.chat = FakeChat(chat_id)
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str, **kwargs) -> None:
        self.replies.append(text)


class FakeUpdate:
    def __init__(self, chat_id: int, text: str) -> None:
        self.effective_chat = FakeChat(chat_id)
        self.effective_message = FakeMessage(chat_id, text)


def configure_test_environment() -> Path:
    base = Path("data") / f"phase8-check-{uuid4().hex[:8]}"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    os.environ["DATA_DIR"] = str(base)
    os.environ["PROJECTS_ROOT"] = str(base / "projects")
    os.environ["SQLITE_DB_PATH"] = str(base / "orchestrator.db")
    os.environ["GRAPH_CHECKPOINT_PATH"] = str(base / "checkpoints.sqlite")
    get_settings.cache_clear()
    return base


async def reset_singletons() -> tuple[EventBus, StateManager]:
    bus = EventBus()
    await bus.reset()
    state_manager = StateManager()
    await state_manager.reset()
    return bus, state_manager


async def seed_projects() -> list[Project]:
    repository = Repository()
    await repository.initialize()
    projects = [
        Project(project_id="proj-a", name="alpha", description="Alpha project", status="active"),
        Project(project_id="proj-b", name="beta", description="Beta project", status="planning"),
        Project(project_id="proj-c", name="gamma", description="Gamma project", status="completed"),
    ]
    for index, project in enumerate(projects, start=1):
        await repository.upsert_project(
            project.model_copy(update={"created_at": f"2026-04-3{index}T10:00:00+00:00", "updated_at": utc_now()})
        )
    await repository.create_sprint(
        Sprint(
            sprint_id="s1-alpha",
            project_id="proj-a",
            number=1,
            sprint_type="contract",
            status="approved",
            review_cycles=1,
            files_written=["api_contract.json", "shared_types.py"],
            started_at="2026-04-30T10:00:00+00:00",
            completed_at="2026-04-30T10:30:00+00:00",
        )
    )
    await repository.create_sprint(
        Sprint(
            sprint_id="s2-alpha",
            project_id="proj-a",
            number=2,
            sprint_type="feature",
            status="approved",
            review_cycles=2,
            files_written=["app.py"],
            started_at="2026-04-30T10:30:00+00:00",
            completed_at="2026-04-30T11:00:00+00:00",
        )
    )
    await repository.create_sprint(
        Sprint(
            sprint_id="s1-beta",
            project_id="proj-b",
            number=1,
            sprint_type="contract",
            status="planning",
            review_cycles=0,
            started_at="2026-04-30T09:00:00+00:00",
            completed_at=None,
        )
    )
    await repository.upsert_file_record(
        FileRecord(
            file_id="fa-1",
            project_id="proj-a",
            sprint_id="s1-alpha",
            path="api_contract.json",
            status="done",
            worker_id="worker_a",
            attempt_count=1,
        )
    )
    await repository.upsert_file_record(
        FileRecord(
            file_id="fa-2",
            project_id="proj-a",
            sprint_id="s2-alpha",
            path="app.py",
            status="done",
            worker_id="worker_b",
            attempt_count=2,
        )
    )
    await repository.upsert_file_record(
        FileRecord(
            file_id="fa-3",
            project_id="proj-a",
            sprint_id="s2-alpha",
            path="broken.py",
            status="failed",
            worker_id="worker_b",
            attempt_count=3,
            last_error="boom",
        )
    )
    await repository.create_worker_failure(
        WorkerFailureLog(
            failure_id="wf-1",
            project_id="proj-a",
            sprint_id="s2-alpha",
            worker_id="worker_b",
            task_type="feature",
            error_message="boom",
            retryable=True,
            retry_count=3,
        )
    )
    return projects


async def check_project_manager_flow() -> CheckResult:
    manager = ProjectManager()
    projects = await manager.list_projects()
    selected = await manager.select_active_project("proj-b")
    fetched = await manager.get_project("beta")
    if len(projects) == 3 and selected and fetched and fetched.project_id == "proj-b":
        return CheckResult("Project Manager", True, "Multi-project list/select/get akisi calisti.")
    return CheckResult("Project Manager", False, f"Project manager akisi bozuk: count={len(projects)} selected={selected} fetched={fetched}")


async def check_cli_and_telegram_project_commands() -> CheckResult:
    bus, state_manager = await reset_singletons()
    await state_manager.set("proj-b", {"project_id": "proj-b", "project_name": "beta", "current_thread_id": "thread-b"})
    context = CommandContext(
        event_bus=bus,
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=state_manager,
        current_state={"project_id": "proj-b", "project_name": "beta", "current_thread_id": "thread-b"},
        active_approval=None,
    )
    cli_projects = await execute_command("/projects", context)
    cli_history = await execute_command("/history alpha", context)
    telegram_context = TelegramHandlerContext(
        event_bus=bus,
        graph_manager=None,
        state_manager=state_manager,
        authorized_chat_id="1001",
    )
    update_projects = FakeUpdate(1001, "/projects")
    update_history = FakeUpdate(1001, "/history alpha")
    await handle_projects(update_projects, telegram_context)
    await handle_history(update_history, telegram_context)
    if (
        cli_projects.ok
        and cli_history.ok
        and "Projects:" in cli_projects.message
        and "History: alpha" in cli_history.message
        and update_projects.effective_message.replies
        and update_history.effective_message.replies
    ):
        return CheckResult("CLI/Telegram Commands", True, "/projects ve /history deterministic cikti verdi.")
    return CheckResult(
        "CLI/Telegram Commands",
        False,
        f"CLI/TG ciktilari eksik: cli={cli_projects.message} / {cli_history.message} tg={update_projects.effective_message.replies} / {update_history.effective_message.replies}",
    )


async def check_project_summary_metrics() -> CheckResult:
    summary = await ProjectManager().project_summary("proj-a")
    if summary and summary.total_sprints == 2 and summary.total_files_written == 2 and "worker_b" in summary.worker_success_rates:
        return CheckResult("Project Summary", True, "Project summary metrikleri repository uzerinden hesaplandi.")
    return CheckResult("Project Summary", False, f"Summary eksik veya hatali: {summary}")


async def check_parallel_isolation() -> CheckResult:
    bus, state_manager = await reset_singletons()
    manager = GraphManager(
        event_bus=bus,
        state_manager=state_manager,
        repository=Repository(),
        approval_guard=ApprovalGuard(),
    )
    await manager.start()
    await state_manager.set("proj-a", {"project_id": "proj-a", "messages": []})
    await state_manager.set("proj-b", {"project_id": "proj-b", "messages": []})
    await manager.register_approval(
        ApprovalRequest(
            approval_id="approval-a",
            project_id="proj-a",
            thread_id="thread-a",
            sprint_id="sprint-1",
            approval_type="plan",
        )
    )
    await manager.register_approval(
        ApprovalRequest(
            approval_id="approval-b",
            project_id="proj-b",
            thread_id="thread-b",
            sprint_id="sprint-1",
            approval_type="plan",
        )
    )
    await bus.emit(
        "plan.approved",
        new_event(
            "plan.approved",
            payload={"approval_id": "approval-a", "decision": "approved"},
            project_id="proj-a",
            thread_id="thread-a",
            sprint_id="sprint-1",
            idempotency_key="approve-a",
        ).model_dump(),
    )
    state_a = await state_manager.get("proj-a")
    state_b = await state_manager.get("proj-b")
    approvals_a = state_a.get("approvals", {})
    approvals_b = state_b.get("approvals", {})
    if "approval-a" in approvals_a and "approval-b" not in approvals_a and not approvals_b:
        return CheckResult("Project Isolation", True, "Parallel project approval routing izolasyonu korudu.")
    return CheckResult("Project Isolation", False, f"Isolation bozuk: A={approvals_a} B={approvals_b}")


async def check_scheduler_fairness() -> CheckResult:
    scheduler = FairScheduler(per_project_limit=1)
    for idx in range(3):
        scheduler.enqueue(ScheduledTask(project_id="proj-a", thread_id=f"ta-{idx}", task_id=f"a-{idx}"))
    for idx in range(2):
        scheduler.enqueue(ScheduledTask(project_id="proj-b", thread_id=f"tb-{idx}", task_id=f"b-{idx}"))
    order = []
    for _ in range(4):
        decision = scheduler.acquire_next()
        if decision.task is None:
            break
        order.append(decision.task.project_id)
        scheduler.release(decision.task.project_id)
    if order[:4] == ["proj-a", "proj-b", "proj-a", "proj-b"]:
        return CheckResult("Scheduler Fairness", True, "Round-robin fairness starvation olmadan calisti.")
    return CheckResult("Scheduler Fairness", False, f"Fairness beklenen sirayi vermedi: {order}")


async def check_concurrency_limit_and_archive() -> CheckResult:
    scheduler = FairScheduler(per_project_limit=1)
    scheduler.enqueue(ScheduledTask(project_id="proj-a", thread_id="ta-1", task_id="a-1"))
    scheduler.enqueue(ScheduledTask(project_id="proj-a", thread_id="ta-2", task_id="a-2"))
    scheduler.enqueue(ScheduledTask(project_id="proj-b", thread_id="tb-1", task_id="b-1"))
    first = scheduler.acquire_next()
    second = scheduler.acquire_next()
    scheduler.archive_project("proj-b")
    third = scheduler.acquire_next()
    if first.task and second.task and first.task.project_id != second.task.project_id and (third.task is None or third.task.project_id != "proj-b"):
        return CheckResult("Concurrency/Archive", True, "Concurrency limit ve archived project izolasyonu enforce edildi.")
    return CheckResult(
        "Concurrency/Archive",
        False,
        f"Concurrency/archive bozuk: first={first.task.project_id if first.task else None} second={second.task.project_id if second.task else None} third={third.task.project_id if third.task else None}",
    )


async def check_rate_limit_policy() -> CheckResult:
    scheduler = FairScheduler(per_project_limit=1)
    scheduler.enqueue(ScheduledTask(project_id="proj-a", thread_id="ta", task_id="a"))

    class RateLimitError(Exception):
        status_code = 429

    outcome = scheduler.handle_provider_error("proj-a", RateLimitError("rate"))
    decision = scheduler.acquire_next()
    if outcome == "throttled" and decision.task is None and decision.reason == "throttled":
        return CheckResult("Rate Limit Policy", True, "Rate-limit sinyalinde project gecici throttle edildi.")
    return CheckResult("Rate Limit Policy", False, f"Throttle policy beklenen gibi degil: outcome={outcome} decision={decision.reason}")


async def run_checks() -> list[CheckResult]:
    configure_test_environment()
    await reset_singletons()
    await seed_projects()
    return [
        await check_project_manager_flow(),
        await check_cli_and_telegram_project_commands(),
        await check_project_summary_metrics(),
        await check_parallel_isolation(),
        await check_scheduler_fairness(),
        await check_concurrency_limit_and_archive(),
        await check_rate_limit_policy(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    print("\n=== PHASE 8 ACCEPTANCE SUMMARY ===")
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
    print(f"PHASE_8_STATUS: {'READY' if fail_count == 0 else 'NOT_READY'}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
