from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from src.config.settings import get_settings
from src.core.approval_guard import ApprovalGuard
from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.scheduler import FairScheduler, ScheduledTask
from src.core.state_manager import StateManager
from src.interfaces.cli.commands import CommandContext, execute_command
from src.interfaces.cli.notifier import CLINotifier
from src.interfaces.telegram.handlers import TelegramHandlerContext, handle_task
from src.storage.models import Project
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


def configure_test_environment() -> None:
    base = Path("data") / f"fullstack-smoke-{uuid4().hex[:8]}"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    os.environ["DATA_DIR"] = str(base)
    os.environ["PROJECTS_ROOT"] = str(base / "projects")
    os.environ["SQLITE_DB_PATH"] = str(base / "orchestrator.db")
    os.environ["GRAPH_CHECKPOINT_PATH"] = str(base / "checkpoints.sqlite")
    os.environ["TELEGRAM_CHAT_ID"] = "1001"
    os.environ["MANAGER_USE_GEMINI"] = "0"
    os.environ["WORKER_USE_STUB"] = "1"
    get_settings.cache_clear()


async def reset_singletons() -> tuple[EventBus, StateManager]:
    bus = EventBus()
    await bus.reset()
    state_manager = StateManager()
    await state_manager.reset()
    return bus, state_manager


async def check_fullstack_flow() -> CheckResult:
    bus, state_manager = await reset_singletons()
    repository = Repository()
    await repository.initialize()
    graph_manager = GraphManager(
        event_bus=bus,
        state_manager=state_manager,
        repository=repository,
        approval_guard=ApprovalGuard(),
    )
    await graph_manager.start()
    await graph_manager.bootstrap_runtime()

    command_context = CommandContext(
        event_bus=bus,
        graph_manager=graph_manager,
        notifier=CLINotifier(),
        state_manager=state_manager,
        current_state=None,
        active_approval=None,
    )
    new_outcome = await execute_command("/new fullstack-alpha", command_context)
    chat_outcome = await execute_command("/r build a smoke web project", command_context)
    project_id = command_context.current_state["project_id"]
    state = await state_manager.get(project_id)
    command_context.current_state = state
    plan_outcome = await execute_command("/plan fullstack-alpha", command_context)
    state = await state_manager.get(project_id)
    approval_id = state["approval_request"]["approval_id"]
    command_context.current_state = state
    command_context.active_approval = state["approval_request"]
    approve_outcome = await execute_command(f"/approve {approval_id}", command_context)
    await asyncio.sleep(0.1)
    final_state = await state_manager.get(project_id)
    await graph_manager.shutdown_runtime()
    if all(item.ok for item in (new_outcome, chat_outcome, plan_outcome, approve_outcome)) and final_state.get("sprint_status") == "approved":
        return CheckResult("Fullstack Flow", True, "New -> chat -> plan -> approval -> worker -> reviewer -> completed akisi bitti.")
    return CheckResult("Fullstack Flow", False, f"Akis tamamlanmadi: state={final_state}")


async def check_cli_telegram_publish_consume() -> CheckResult:
    bus, state_manager = await reset_singletons()
    repository = Repository()
    await repository.initialize()
    await repository.upsert_project(Project(project_id="iface-project", name="iface", description="iface", status="active", metadata={"selected": True}))
    consumed: list[str] = []

    async def consume(payload: dict) -> None:
        consumed.append(payload["payload"]["task_description"])

    await bus.subscribe("task.received", consume)
    cli_context = CommandContext(
        event_bus=bus,
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=state_manager,
        current_state={"project_id": "iface-project", "project_name": "iface"},
        active_approval=None,
    )
    await execute_command("/task from-cli", cli_context)
    telegram_context = TelegramHandlerContext(
        event_bus=bus,
        graph_manager=None,
        state_manager=state_manager,
        authorized_chat_id="1001",
    )
    await handle_task(FakeUpdate(1001, "/task from-telegram"), telegram_context)
    if consumed == ["from-cli", "from-telegram"]:
        return CheckResult("CLI/Telegram Publish", True, "CLI ve Telegram task event publish/consume zinciri dogrulandi.")
    return CheckResult("CLI/Telegram Publish", False, f"Beklenen consume sirasi yok: {consumed}")


async def check_scheduler_fairness_smoke() -> CheckResult:
    scheduler = FairScheduler(per_project_limit=1)
    for project_id in ("a", "b", "c"):
        for index in range(2):
            scheduler.enqueue(ScheduledTask(project_id=project_id, thread_id=f"{project_id}-{index}", task_id=f"{project_id}-{index}"))
    order = []
    for _ in range(6):
        decision = scheduler.acquire_next()
        if decision.task is None:
            break
        order.append(decision.task.project_id)
        scheduler.release(decision.task.project_id)
    if order[:6] == ["a", "b", "c", "a", "b", "c"]:
        return CheckResult("Scheduler Fairness", True, "Multi-project fairness smoke round-robin sirasi korudu.")
    return CheckResult("Scheduler Fairness", False, f"Fairness smoke bozuk: {order}")


async def run_checks() -> list[CheckResult]:
    configure_test_environment()
    return [
        await check_fullstack_flow(),
        await check_cli_telegram_publish_consume(),
        await check_scheduler_fairness_smoke(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    print("\n=== FULLSTACK SMOKE SUMMARY ===")
    print(f"TOTAL: {len(results)}")
    print(f"PASS: {pass_count}")
    print(f"FAIL: {fail_count}")
    if fail_count:
        print("FAIL_REASONS:")
        for item in results:
            if not item.passed:
                print(f"- {item.name}: {item.detail}")
    else:
        print("FAIL_REASONS: none")
    print(f"FULLSTACK_STATUS: {'PASS' if fail_count == 0 else 'FAIL'}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
