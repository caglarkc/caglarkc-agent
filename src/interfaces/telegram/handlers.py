from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.project_manager import ProjectManager
from src.core.state_manager import StateManager
from src.interfaces.telegram.keyboards import decode_approval_callback
from src.interfaces.telegram.state_view import format_telegram_history, format_telegram_projects, format_telegram_status


HELP_TEXT = "\n".join(
    [
        "/task <metin>",
        "/status",
        "/projects",
        "/history <proje>",
        "/cancel [approval_id] [reason]",
        "/help",
    ]
)


@dataclass
class TelegramHandlerContext:
    event_bus: EventBus
    graph_manager: GraphManager | None
    state_manager: StateManager
    authorized_chat_id: str


def _is_authorized(chat_id: int | str | None, authorized_chat_id: str) -> bool:
    return chat_id is not None and str(chat_id) == str(authorized_chat_id)


async def _latest_state(state_manager: StateManager) -> dict[str, Any] | None:
    snapshot = await state_manager.snapshot()
    if not snapshot:
        return None
    _, state = next(reversed(snapshot.items()))
    return state if isinstance(state, dict) else None


async def ensure_authorized(update: Any, context: TelegramHandlerContext, *, is_callback: bool = False) -> bool:
    chat_id = None
    if is_callback:
        chat_id = getattr(getattr(update, "callback_query", None), "message", None)
        chat_id = getattr(getattr(chat_id, "chat", None), "id", None)
    else:
        chat_id = getattr(getattr(update, "effective_chat", None), "id", None)
    if _is_authorized(chat_id, context.authorized_chat_id):
        return True
    if is_callback and getattr(update, "callback_query", None) is not None:
        await update.callback_query.answer("Yetkisiz istek.", show_alert=True)
    elif getattr(update, "effective_message", None) is not None:
        await update.effective_message.reply_text("Bu chat yetkili degil.")
    return False


async def handle_task(update: Any, telegram_context: TelegramHandlerContext) -> None:
    if not await ensure_authorized(update, telegram_context):
        return
    text = getattr(getattr(update, "effective_message", None), "text", "") or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await update.effective_message.reply_text("Kullanim: /task <metin>")
        return
    state = await _latest_state(telegram_context.state_manager) or {}
    active_project = await ProjectManager().active_project()
    task_text = parts[1].strip()
    await telegram_context.event_bus.publish(
        "task.received",
        new_event(
            "task.received",
            payload={"task_description": task_text},
            project_id=(active_project.project_id if active_project else state.get("project_id")),
            thread_id=state.get("current_thread_id"),
            correlation_id=(active_project.project_id if active_project else state.get("project_id")),
        ).model_dump(),
    )
    await update.effective_message.reply_text(f"Gorev alindi: {task_text}")


async def handle_status(update: Any, telegram_context: TelegramHandlerContext) -> None:
    if not await ensure_authorized(update, telegram_context):
        return
    state = await _latest_state(telegram_context.state_manager)
    active_approval = state.get("approval_request") if isinstance(state, dict) else None
    await update.effective_message.reply_text(format_telegram_status(state, active_approval=active_approval))


async def handle_projects(update: Any, telegram_context: TelegramHandlerContext) -> None:
    if not await ensure_authorized(update, telegram_context):
        return
    manager = ProjectManager()
    projects = await manager.list_projects(active_only=True)
    active = await manager.active_project()
    await update.effective_message.reply_text(
        format_telegram_projects(projects, active_project_id=active.project_id if active else None)
    )


async def handle_history(update: Any, telegram_context: TelegramHandlerContext) -> None:
    if not await ensure_authorized(update, telegram_context):
        return
    text = getattr(getattr(update, "effective_message", None), "text", "") or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await update.effective_message.reply_text("Kullanim: /history <proje>")
        return
    manager = ProjectManager()
    project = await manager.get_project(parts[1].strip())
    if project is None:
        await update.effective_message.reply_text(f"Proje bulunamadi: {parts[1].strip()}")
        return
    history = await manager.project_history(project.project_id)
    await update.effective_message.reply_text(format_telegram_history(project.name, history))


async def handle_cancel(update: Any, telegram_context: TelegramHandlerContext) -> None:
    if not await ensure_authorized(update, telegram_context):
        return
    text = getattr(getattr(update, "effective_message", None), "text", "") or ""
    parts = text.split()
    approval_id = parts[1] if len(parts) > 1 else None
    reason = " ".join(parts[2:]) if len(parts) > 2 else ""
    state = await _latest_state(telegram_context.state_manager) or {}
    active_approval = state.get("approval_request") if isinstance(state.get("approval_request"), dict) else None
    if approval_id is None and active_approval is not None:
        approval_id = active_approval.get("approval_id")
    if not approval_id:
        await update.effective_message.reply_text("Aktif approval bulunamadi.")
        return
    guard = telegram_context.graph_manager.approval_guard if telegram_context.graph_manager else None
    request = await guard.get_approval(approval_id) if guard is not None else None
    if request is None:
        await update.effective_message.reply_text("Bu onay artik gecerli degil.")
        return
    if request.status != "pending":
        await update.effective_message.reply_text("Bu karar zaten islenmis.")
        return
    if datetime.fromisoformat(request.expires_at) <= datetime.now(timezone.utc):
        await update.effective_message.reply_text("Bu onay artik gecerli degil.")
        return
    await telegram_context.event_bus.publish(
        "plan.cancelled",
        new_event(
            "plan.cancelled",
            payload={"approval_id": approval_id, "decision": "cancelled", "reason": reason},
            project_id=request.project_id,
            thread_id=request.thread_id,
            sprint_id=request.sprint_id,
            correlation_id=request.project_id,
            idempotency_key=f"cancel-{approval_id}",
        ).model_dump(),
    )
    await update.effective_message.reply_text(f"Approval iptal edildi: {approval_id}")


async def handle_help(update: Any, telegram_context: TelegramHandlerContext) -> None:
    if not await ensure_authorized(update, telegram_context):
        return
    await update.effective_message.reply_text(HELP_TEXT)


async def handle_approval_callback(update: Any, telegram_context: TelegramHandlerContext) -> None:
    if not await ensure_authorized(update, telegram_context, is_callback=True):
        return
    query = update.callback_query
    payload = decode_approval_callback(query.data)
    approval_id = payload["approval_id"]
    decision = payload["decision"]
    guard = telegram_context.graph_manager.approval_guard if telegram_context.graph_manager else None
    request = await guard.get_approval(approval_id) if guard is not None else None
    if request is None:
        await query.answer("Bu onay artik gecerli degil", show_alert=True)
        return
    if request.status != "pending":
        await query.answer("Karar zaten islendi", show_alert=True)
        return
    if datetime.fromisoformat(request.expires_at) <= datetime.now(timezone.utc):
        await query.answer("Bu onay artik gecerli degil", show_alert=True)
        return
    event_type = {
        "approved": "plan.approved",
        "rejected": "plan.rejected",
        "cancelled": "plan.cancelled",
    }[decision]
    await telegram_context.event_bus.publish(
        event_type,
        new_event(
            event_type,
            payload={"approval_id": approval_id, "decision": decision},
            project_id=request.project_id,
            thread_id=request.thread_id,
            sprint_id=request.sprint_id,
            correlation_id=request.project_id,
            idempotency_key=payload["idempotency_key"],
        ).model_dump(),
    )
    await query.answer(f"Karar iletildi: {decision}")
    await query.edit_message_text(f"Approval {approval_id}: {decision}")


def register_handlers(application: Any, telegram_context: TelegramHandlerContext) -> None:
    from telegram.ext import CallbackQueryHandler, CommandHandler

    async def task_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_task(update, telegram_context)

    async def status_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_status(update, telegram_context)

    async def cancel_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_cancel(update, telegram_context)

    async def projects_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_projects(update, telegram_context)

    async def history_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_history(update, telegram_context)

    async def help_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_help(update, telegram_context)

    async def callback_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_approval_callback(update, telegram_context)

    application.add_handler(CommandHandler("task", task_wrapper))
    application.add_handler(CommandHandler("status", status_wrapper))
    application.add_handler(CommandHandler("projects", projects_wrapper))
    application.add_handler(CommandHandler("history", history_wrapper))
    application.add_handler(CommandHandler("cancel", cancel_wrapper))
    application.add_handler(CommandHandler("help", help_wrapper))
    application.add_handler(CallbackQueryHandler(callback_wrapper, pattern=r"^ap:"))
