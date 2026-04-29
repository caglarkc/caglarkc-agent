from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from src.core.approval_guard import ApprovalGuard
from src.core.contracts import ApprovalRequest, new_event, utc_now
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.state_manager import StateManager
from src.interfaces.telegram.bot import OrchestratorTelegramBot
from src.interfaces.telegram.handlers import (
    TelegramHandlerContext,
    handle_approval_callback,
    handle_cancel,
    handle_status,
    handle_task,
    register_handlers,
)
from src.interfaces.telegram.notifier import TelegramNotifier
from src.interfaces.telegram.state_view import format_telegram_status


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


class FakeApp:
    def __init__(self) -> None:
        self.handlers: list[Any] = []
        self.bot = FakeBot()
        self.initialized = False
        self.started = False

    def add_handler(self, handler: Any) -> None:
        self.handlers.append(handler)

    async def initialize(self) -> None:
        self.initialized = True

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.started = False

    async def shutdown(self) -> None:
        self.initialized = False


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send_message(self, chat_id: str, text: str, **kwargs: Any) -> None:
        self.messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})


class FakeChat:
    def __init__(self, chat_id: int) -> None:
        self.id = chat_id


class FakeMessage:
    def __init__(self, chat_id: int, text: str = "") -> None:
        self.chat = FakeChat(chat_id)
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text: str, **kwargs: Any) -> None:
        self.replies.append(text)


class FakeCallbackQuery:
    def __init__(self, chat_id: int, data: str) -> None:
        self.message = FakeMessage(chat_id)
        self.data = data
        self.answers: list[str] = []
        self.edited_text: str | None = None

    async def answer(self, text: str, show_alert: bool = False) -> None:
        self.answers.append(text)

    async def edit_message_text(self, text: str) -> None:
        self.edited_text = text


class FakeUpdate:
    def __init__(self, chat_id: int, text: str = "", *, callback_data: str | None = None) -> None:
        self.effective_chat = FakeChat(chat_id)
        self.effective_message = FakeMessage(chat_id, text)
        self.callback_query = FakeCallbackQuery(chat_id, callback_data) if callback_data is not None else None


async def check_bot_bootstrap() -> CheckResult:
    app = FakeApp()
    bot = OrchestratorTelegramBot(
        token="dummy-token",
        authorized_chat_id="1001",
        application=app,
    )
    bot.register_handlers()
    if len(app.handlers) >= 5:
        return CheckResult("Bot Bootstrap", True, "Bot bootstrap oldu ve handler'lar register edildi.")
    return CheckResult("Bot Bootstrap", False, f"Handler register eksik: {len(app.handlers)}")


async def check_authorized_and_unauthorized_commands() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    graph_manager = GraphManager(event_bus=bus, approval_guard=ApprovalGuard())
    context = TelegramHandlerContext(
        event_bus=bus,
        graph_manager=graph_manager,
        state_manager=StateManager(),
        authorized_chat_id="1001",
    )
    await context.state_manager.set(
        "project-auth",
        {"project_id": "project-auth", "project_name": "auth-project", "current_thread_id": "thread-auth"},
    )
    authorized = FakeUpdate(1001, "/task build auth")
    unauthorized = FakeUpdate(9999, "/task should fail")
    await handle_task(authorized, context)
    events_after_authorized = await bus.get_recent_events()
    await bus.reset()
    await handle_task(unauthorized, context)
    events_after_unauthorized = await bus.get_recent_events()
    if events_after_authorized and not events_after_unauthorized and unauthorized.effective_message.replies:
        return CheckResult("Auth Control", True, "Yetkili chat komutlari calisti, yetkisiz chat bloklandi.")
    return CheckResult(
        "Auth Control",
        False,
        f"Auth davranisi bozuk: auth_events={events_after_authorized}, unauth_events={events_after_unauthorized}",
    )


async def check_task_publish() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    context = TelegramHandlerContext(
        event_bus=bus,
        graph_manager=None,
        state_manager=StateManager(),
        authorized_chat_id="1001",
    )
    await context.state_manager.set("project-task", {"project_id": "project-task", "current_thread_id": "thread-task"})
    update = FakeUpdate(1001, "/task create report")
    await handle_task(update, context)
    events = await bus.get_recent_events()
    if events and events[-1]["event_name"] == "task.received":
        return CheckResult("Task Command", True, "/task task.received publish etti.")
    return CheckResult("Task Command", False, f"/task publish etmedi: {events}")


async def check_approval_keyboard_message() -> CheckResult:
    sent: list[dict[str, Any]] = []

    async def send_message(text: str, kwargs: dict[str, Any]) -> None:
        sent.append({"text": text, "kwargs": kwargs})

    notifier = TelegramNotifier(send_message=send_message)
    payload = new_event(
        "plan.approval_needed",
        payload={
            "approval_id": "approval-keyboard",
            "project_id": "project-1",
            "thread_id": "thread-1",
            "approval_type": "plan",
            "requested_at": utc_now().isoformat(),
            "expires_at": (utc_now() + timedelta(minutes=15)).isoformat(),
            "status": "pending",
        },
        project_id="project-1",
        thread_id="thread-1",
        sprint_id="sprint-1",
        idempotency_key="approval-keyboard",
    ).model_dump()
    await notifier.handle_event(payload)
    if sent and sent[0]["kwargs"].get("reply_markup") is not None:
        return CheckResult("Approval Keyboard", True, "plan.approval_needed inline keyboard mesaji uretti.")
    return CheckResult("Approval Keyboard", False, f"Keyboard mesaji uretilmedi: {sent}")


async def check_callback_decisions() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    graph_manager = GraphManager(event_bus=bus, approval_guard=ApprovalGuard())
    context = TelegramHandlerContext(
        event_bus=bus,
        graph_manager=graph_manager,
        state_manager=StateManager(),
        authorized_chat_id="1001",
    )
    requests = [
        ("approval-yes", "approved"),
        ("approval-no", "rejected"),
        ("approval-cancel", "cancelled"),
    ]
    for approval_id, decision in requests:
        await graph_manager.register_approval(
            ApprovalRequest(
                approval_id=approval_id,
                project_id="project-callback",
                thread_id="thread-callback",
                sprint_id="sprint-1",
                approval_type="plan",
            )
        )
        callback_data = f"ap:{decision}:{approval_id}:tg-{decision[:1]}-123456789abc"
        update = FakeUpdate(1001, callback_data=callback_data)
        await handle_approval_callback(update, context)
    history = await bus.get_recent_events()
    event_names = [item["event_name"] for item in history]
    if {"plan.approved", "plan.rejected", "plan.cancelled"}.issubset(set(event_names)):
        return CheckResult("Callback Decisions", True, "Callback onay/reddet/iptal dogru eventleri uretti.")
    return CheckResult("Callback Decisions", False, f"Callback eventleri eksik: {event_names}")


async def check_stale_callback_safe() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    graph_manager = GraphManager(event_bus=bus, approval_guard=ApprovalGuard())
    context = TelegramHandlerContext(
        event_bus=bus,
        graph_manager=graph_manager,
        state_manager=StateManager(),
        authorized_chat_id="1001",
    )
    approval_id = "approval-stale"
    await graph_manager.register_approval(
        ApprovalRequest(
            approval_id=approval_id,
            project_id="project-stale",
            thread_id="thread-stale",
            sprint_id="sprint-1",
            approval_type="plan",
            expires_at=(utc_now() - timedelta(minutes=1)).isoformat(),
        )
    )
    update = FakeUpdate(1001, callback_data=f"ap:approved:{approval_id}:tg-a-stale")
    await handle_approval_callback(update, context)
    history = await bus.get_recent_events()
    if not history and update.callback_query.answers and "gecerli degil" in update.callback_query.answers[-1]:
        return CheckResult("Stale Callback", True, "Stale callback state degistirmeden reddedildi.")
    return CheckResult("Stale Callback", False, f"Stale callback guvensiz: history={history}, answers={update.callback_query.answers}")


async def check_status_summary() -> CheckResult:
    state = {
        "project_name": "status-project",
        "current_sprint": 3,
        "sprint_type": "feature",
        "sprint_status": "revision",
        "worker_queue": [1, 2, 3],
        "worker_status": {"worker_a": "idle", "worker_b": "working"},
        "last_heartbeat_at": utc_now().isoformat(),
        "stalled_since": None,
        "approval_request": {"approval_id": "approval-status", "approval_type": "plan", "status": "pending"},
    }
    text = format_telegram_status(state, active_approval=state["approval_request"])
    if "Proje: status-project" in text and "Approval: approval-status" in text:
        return CheckResult("Status View", True, "/status deterministic ozet uretıyor.")
    return CheckResult("Status View", False, f"Status view beklenen formatta degil: {text}")


async def check_notifier_flow() -> CheckResult:
    bus = EventBus()
    await bus.reset()
    sent: list[str] = []

    async def send_message(text: str, kwargs: dict[str, Any]) -> None:
        sent.append(text)

    notifier = TelegramNotifier(send_message=send_message, event_bus=bus)
    await notifier.subscribe()
    await bus.emit(
        "sprint.completed",
        new_event("sprint.completed", payload={"result": "approved"}, project_id="p", thread_id="t").model_dump(),
    )
    await bus.emit(
        "system.stalled",
        new_event("system.stalled", payload={"reason": "silence"}, project_id="p", thread_id="t").model_dump(),
    )
    await bus.emit(
        "error.occurred",
        new_event("error.occurred", payload={"message": "boom"}, project_id="p", thread_id="t").model_dump(),
    )
    if len(sent) >= 3 and any("Sprint tamamlandi" in text for text in sent) and any("duraksadi" in text for text in sent):
        return CheckResult("Notifier Flow", True, "Sprint/stalled/error notifier akisi calisti.")
    return CheckResult("Notifier Flow", False, f"Notifier eventleri beklenen mesajlari uretmedi: {sent}")


async def run_checks() -> list[CheckResult]:
    return [
        await check_bot_bootstrap(),
        await check_authorized_and_unauthorized_commands(),
        await check_task_publish(),
        await check_approval_keyboard_message(),
        await check_callback_decisions(),
        await check_stale_callback_safe(),
        await check_status_summary(),
        await check_notifier_flow(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    print("\n=== PHASE 6 ACCEPTANCE SUMMARY ===")
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
    print(f"PHASE_6_STATUS: {'READY' if fail_count == 0 else 'NOT_READY'}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
