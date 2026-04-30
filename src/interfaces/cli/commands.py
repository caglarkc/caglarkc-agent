from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.core.contracts import new_event
from src.core.ai_scanner import AIScanner
from src.core.project_manager import ProjectManager
from src.graph.state import build_initial_state
from src.interfaces.cli.notifier import CLINotifier
from src.interfaces.cli.state_view import format_project_history, format_projects_listing, format_status_summary


TERMINAL_TASK_STATUSES = {"closed", "rejected", "cancelled"}
PLAN_FROM_CONVERSATION_PROMPT = (
    "Bu projenin sohbet gecmisindeki istekleri toparla. Kullanıcının hedefini netlestir, "
    "eksik belirsizlikleri minimumda tutarak uygulanabilir bir proje planina cevir. "
    "Cikacak isi 1-3 AI worker gorevine bol, dosya listesini ve bagimliliklari belirle. "
    "Bu cevap planlama moduna gecis icindir; JSON plan alanini mutlaka doldur ve execution_intent=apply dondur."
)


def _ensure_thread_id(state: dict[str, Any]) -> str:
    if state.get("planning_status") in TERMINAL_TASK_STATUSES:
        thread_id = f"thread-{uuid4().hex}"
        state.update(
            {
                "planning_thread_id": thread_id,
                "current_thread_id": thread_id,
                "planning_status": "idle",
                "manager_reply": None,
                "draft_plan": None,
                "conversation_history": [],
                "worker_queue": [],
                "approval_request": None,
                "awaiting_approval": False,
                "active_approval_id": None,
            }
        )
        return thread_id
    thread_id = state.get("planning_thread_id") or state.get("current_thread_id")
    if isinstance(thread_id, str) and thread_id.strip():
        return thread_id.strip()
    thread_id = f"thread-{uuid4().hex}"
    state["planning_thread_id"] = thread_id
    state["current_thread_id"] = thread_id
    return thread_id


HELP_TEXT = "\n".join(
    [
        "/task <metin>",
        "/new <proje adi>",
        "/resume [project_id veya proje adi]",
        "/r <mesaj>",
        "/plan [project_id veya proje adi]",
        "/apply [istege bagli not]",
        "/status",
        "/approve [approval_id]  (yalnızca olay günlüğünde plan onayı istendiğinde veya Approval panelde ID varken)",
        "/reject [approval_id] [reason]",
        "/cancel [approval_id] [reason]",
        "/close [reason]",
        "/projects",
        "/history <proje>",
        "/project use <id>",
        "/scan",
        "/help",
    ]
)


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    args: list[str]
    raw: str


@dataclass
class CommandContext:
    event_bus: Any
    graph_manager: Any | None
    notifier: CLINotifier
    state_manager: Any
    current_state: dict[str, Any] | None
    active_approval: dict[str, Any] | None


@dataclass
class CommandOutcome:
    ok: bool
    message: str
    level: str = "info"


def parse_command(raw: str) -> ParsedCommand:
    text = raw.strip()
    if not text:
        return ParsedCommand(name="empty", args=[], raw=raw)
    if not text.startswith("/"):
        return ParsedCommand(name="invalid", args=[text], raw=raw)
    parts = text.split()
    return ParsedCommand(name=parts[0][1:].lower(), args=parts[1:], raw=raw)


async def execute_command(raw: str, context: CommandContext) -> CommandOutcome:
    command = parse_command(raw)
    if command.name == "empty":
        return CommandOutcome(ok=False, message="Empty command.", level="warning")
    if command.name == "invalid":
        return CommandOutcome(ok=False, message=f"Unknown input. Use /help.\n{HELP_TEXT}", level="error")
    if command.name == "help":
        return CommandOutcome(ok=True, message=HELP_TEXT)
    if command.name == "new":
        return await _handle_new_command(command, context)
    if command.name == "resume":
        return await _handle_resume_command(command, context)
    if command.name == "r":
        return await _publish_chat_message(command, context, command_name="/r")
    if command.name == "plan":
        return await _handle_plan_command(command, context)
    if command.name == "task":
        return await _publish_chat_message(command, context, command_name="/task")
    if command.name == "apply":
        state = context.current_state or {}
        thread_id = _ensure_thread_id(state)
        active_project = await ProjectManager().active_project()
        apply_note = " ".join(command.args).strip()
        task_text = apply_note or state.get("task_description") or "apply current draft"
        project_id = active_project.project_id if active_project else state.get("project_id")
        await context.event_bus.publish(
            "task.received",
            new_event(
                "task.received",
                payload={
                    "task_description": task_text,
                    "execution_requested": True,
                    "task_id": thread_id,
                    "suppress_user_turn": not bool(apply_note),
                },
                project_id=project_id,
                thread_id=thread_id,
                correlation_id=project_id,
            ).model_dump(),
        )
        return CommandOutcome(ok=True, message=f"Current draft sent for execution review [{thread_id}].")
    if command.name == "status":
        return CommandOutcome(
            ok=True,
            message=format_status_summary(context.current_state, active_approval=context.active_approval),
        )
    if command.name == "scan":
        try:
            results = await AIScanner().scan_all()
            lines = ["AI Provider Durumu:"]
            for result in results:
                status = "✓" if result.available else "✗"
                lines.append(f"{status} {result.provider}  {result.model_name}  {result.detail}")
            return CommandOutcome(ok=True, message="\n".join(lines))
        except Exception as exc:
            return CommandOutcome(ok=False, message=f"AI Provider Durumu alinamadi: {exc}", level="error")
    if command.name == "close":
        return await _close_current_task(command, context, status="closed")
    if command.name == "projects":
        return await _handle_projects_command()
    if command.name == "history":
        return await _handle_history_command(command)
    if command.name == "project":
        return await _handle_project_command(command, context)
    if command.name in {"approve", "reject", "cancel"}:
        return await _handle_approval_command(command, context)
    return CommandOutcome(ok=False, message=f"Unknown command: /{command.name}\n{HELP_TEXT}", level="error")


async def _handle_projects_command() -> CommandOutcome:
    manager = ProjectManager()
    projects = await manager.list_projects(active_only=True)
    active = await manager.active_project()
    return CommandOutcome(
        ok=True,
        message=format_projects_listing(projects, active_project_id=active.project_id if active else None),
    )


async def _persist_state(context: CommandContext, project_id: str, state: dict[str, Any]) -> None:
    if hasattr(context.state_manager, "set"):
        await context.state_manager.set(project_id, state)
    elif hasattr(context.state_manager, "update"):
        await context.state_manager.update(project_id, state)
    if hasattr(context.state_manager, "flush_to_disk"):
        await context.state_manager.flush_to_disk()


async def _state_for_project(context: CommandContext, project_id: str) -> dict[str, Any]:
    if hasattr(context.state_manager, "get"):
        state = await context.state_manager.get(project_id, {})
        if isinstance(state, dict):
            return state
    snapshot = await context.state_manager.snapshot() if hasattr(context.state_manager, "snapshot") else {}
    state = snapshot.get(project_id, {}) if isinstance(snapshot, dict) else {}
    return state if isinstance(state, dict) else {}


async def _latest_live_state(context: CommandContext) -> dict[str, Any] | None:
    snapshot = await context.state_manager.snapshot() if hasattr(context.state_manager, "snapshot") else {}
    if not isinstance(snapshot, dict):
        return None
    candidates = [item for item in snapshot.values() if isinstance(item, dict)]
    live = [item for item in candidates if item.get("planning_status") not in TERMINAL_TASK_STATUSES]
    return (live or candidates)[-1] if (live or candidates) else None


async def _select_project_state(context: CommandContext, project_ref: str | None = None) -> tuple[Any, dict[str, Any]]:
    manager = ProjectManager()
    project = await manager.get_project(project_ref) if project_ref else await manager.active_project()
    if project is None and not project_ref:
        state = await _latest_live_state(context)
        if state and state.get("project_id"):
            project = await manager.get_project(state["project_id"])
    if project is None:
        raise LookupError(project_ref or "active project")
    await manager.select_active_project(project.project_id)
    state = await _state_for_project(context, project.project_id)
    if not state:
        thread_id = f"thread-{uuid4().hex}"
        state = build_initial_state(
            project_name=project.name,
            task_description="",
            project_id=project.project_id,
            current_thread_id=thread_id,
        )
        state["planning_status"] = "chat_ready"
        await _persist_state(context, project.project_id, state)
    context.current_state = state
    context.active_approval = state.get("approval_request") if state.get("awaiting_approval") else None
    return project, state


async def _handle_new_command(command: ParsedCommand, context: CommandContext) -> CommandOutcome:
    if not command.args:
        return CommandOutcome(ok=False, message="Usage: /new <proje adi>", level="error")
    name = " ".join(command.args).strip()
    try:
        project = await ProjectManager().create_project(name, selected=True)
    except ValueError as exc:
        return CommandOutcome(ok=False, message=str(exc), level="error")
    thread_id = f"thread-{uuid4().hex}"
    state = build_initial_state(
        project_name=project.name,
        task_description="",
        project_id=project.project_id,
        current_thread_id=thread_id,
    )
    state["planning_status"] = "chat_ready"
    await _persist_state(context, project.project_id, state)
    context.current_state = state
    context.active_approval = None
    return CommandOutcome(ok=True, message=f"New project: {project.project_id} | {project.name} | thread={thread_id}")


async def _handle_resume_command(command: ParsedCommand, context: CommandContext) -> CommandOutcome:
    project_ref = " ".join(command.args).strip() or None
    try:
        project, state = await _select_project_state(context, project_ref)
    except LookupError:
        return CommandOutcome(ok=False, message=f"Project not found: {project_ref or 'active/latest'}", level="warning")
    thread_id = state.get("planning_thread_id") or state.get("current_thread_id")
    return CommandOutcome(ok=True, message=f"Resumed: {project.project_id} | {project.name} | thread={thread_id}")


async def _publish_chat_message(command: ParsedCommand, context: CommandContext, *, command_name: str) -> CommandOutcome:
    if not command.args:
        return CommandOutcome(ok=False, message=f"Usage: {command_name} <mesaj>", level="error")
    task_text = " ".join(command.args)
    state = context.current_state
    if not state or not state.get("project_id"):
        try:
            _, state = await _select_project_state(context)
        except LookupError:
            return CommandOutcome(ok=False, message="Once /new <proje adi> ile proje olustur veya /resume ile proje sec.", level="warning")
    thread_id = _ensure_thread_id(state)
    project_id = state.get("project_id")
    if not project_id:
        return CommandOutcome(ok=False, message="Aktif proje yok. Once /new <proje adi> kullan.", level="warning")
    await context.event_bus.publish(
        "task.received",
        new_event(
            "task.received",
            payload={"task_description": task_text, "task_id": thread_id, "chat_message": True},
            project_id=project_id,
            thread_id=thread_id,
            correlation_id=project_id,
        ).model_dump(),
    )
    return CommandOutcome(ok=True, message=f"Message queued [{thread_id}]: {task_text}")


async def _handle_plan_command(command: ParsedCommand, context: CommandContext) -> CommandOutcome:
    project_ref = " ".join(command.args).strip() or None
    try:
        project, state = await _select_project_state(context, project_ref)
    except LookupError:
        return CommandOutcome(ok=False, message=f"Project not found: {project_ref or 'active/latest'}", level="warning")
    if not state.get("conversation_history"):
        return CommandOutcome(ok=False, message="Plan icin sohbet gecmisi yok. Once /r ile projeyi anlat.", level="warning")
    thread_id = _ensure_thread_id(state)
    await context.event_bus.publish(
        "task.received",
        new_event(
            "task.received",
            payload={
                "task_description": PLAN_FROM_CONVERSATION_PROMPT,
                "execution_requested": True,
                "task_id": thread_id,
                "suppress_user_turn": True,
                "plan_from_conversation": True,
            },
            project_id=project.project_id,
            thread_id=thread_id,
            correlation_id=project.project_id,
        ).model_dump(),
    )
    return CommandOutcome(ok=True, message=f"Planning requested [{thread_id}]: {project.project_id} | {project.name}")


async def _handle_history_command(command: ParsedCommand) -> CommandOutcome:
    if not command.args:
        return CommandOutcome(ok=False, message="Usage: /history <proje>", level="error")
    manager = ProjectManager()
    project_ref = " ".join(command.args)
    project = await manager.get_project(project_ref)
    if project is None:
        return CommandOutcome(ok=False, message=f"Project not found: {project_ref}", level="warning")
    history = await manager.project_history(project.project_id)
    return CommandOutcome(ok=True, message=format_project_history(project.name, history))


async def _handle_project_command(command: ParsedCommand, context: CommandContext) -> CommandOutcome:
    if len(command.args) != 2 or command.args[0] != "use":
        return CommandOutcome(ok=False, message="Usage: /project use <id>", level="error")
    manager = ProjectManager()
    project = await manager.select_active_project(command.args[1])
    if project is None:
        return CommandOutcome(ok=False, message=f"Project not found: {command.args[1]}", level="warning")
    if context.current_state is not None:
        context.current_state["project_id"] = project.project_id
        context.current_state["project_name"] = project.name
    return CommandOutcome(ok=True, message=f"Active project set: {project.project_id} | {project.name}")


async def _handle_approval_command(command: ParsedCommand, context: CommandContext) -> CommandOutcome:
    active = context.active_approval
    guard = context.graph_manager.approval_guard if context.graph_manager is not None else None
    if command.name in {"reject", "cancel"} and active is None:
        explicit_request = None
        if guard is not None and command.args:
            explicit_request = await guard.get_approval(command.args[0])
        if explicit_request is None:
            return await _close_current_task(command, context, status={"reject": "rejected", "cancel": "cancelled"}[command.name])
    approval_id: str | None = command.args[0] if command.args else None
    reason = " ".join(command.args[1:]) if len(command.args) > 1 else ""
    if approval_id is None and active is not None:
        approval_id = active.get("approval_id")
    if not approval_id:
        if command.name in {"reject", "cancel"}:
            return await _close_current_task(command, context, status={"reject": "rejected", "cancel": "cancelled"}[command.name])
        return CommandOutcome(
            ok=False,
            message=(
                "Bekleyen plan onayı yok. Akış: /task → günlükte 'Plan üretildi — onay gerekli' "
                "mesajını ve Approval paneldeki ID'yi görmelisin; sprint zaten bittiyse /approve gerekmez."
            ),
            level="warning",
        )

    if guard is not None:
        request = await guard.get_approval(approval_id)
        if request is None or request.status != "pending":
            return CommandOutcome(ok=False, message=f"Approval {approval_id} is stale or expired.", level="warning")
        if datetime.fromisoformat(request.expires_at) <= datetime.now(timezone.utc):
            return CommandOutcome(ok=False, message=f"Approval {approval_id} is stale or expired.", level="warning")
    else:
        request = None

    event_type = {
        "approve": "plan.approved",
        "reject": "plan.rejected",
        "cancel": "plan.cancelled",
    }[command.name]
    decision = {
        "approve": "approved",
        "reject": "rejected",
        "cancel": "cancelled",
    }[command.name]
    project_id = request.project_id if request is not None else (context.current_state or {}).get("project_id")
    thread_id = request.thread_id if request is not None else (context.current_state or {}).get("current_thread_id")
    sprint_id = request.sprint_id if request is not None else None
    payload = {"approval_id": approval_id, "decision": decision}
    if reason:
        payload["reason"] = reason
    await context.event_bus.publish(
        event_type,
        new_event(
            event_type,
            payload=payload,
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
            correlation_id=project_id,
            idempotency_key=f"{decision}-{approval_id}-{uuid4()}",
        ).model_dump(),
    )
    return CommandOutcome(ok=True, message=f"{decision} event sent for approval {approval_id}")


async def _close_current_task(command: ParsedCommand, context: CommandContext, *, status: str) -> CommandOutcome:
    state = context.current_state or {}
    project_id = state.get("project_id")
    thread_id = state.get("planning_thread_id") or state.get("current_thread_id")
    if not project_id or not thread_id:
        return CommandOutcome(ok=False, message="Kapatilacak aktif task/thread bulunamadi.", level="warning")

    reason = " ".join(command.args).strip()
    updates = {
        "planning_status": status,
        "sprint_status": status,
        "awaiting_approval": False,
        "approval_type": "",
        "active_approval_id": None,
        "approval_request": None,
        "execution_requested": False,
        "suppress_user_turn": False,
        "worker_queue": [],
        "active_assignment": None,
        "active_assignments": {},
        "manager_reply": f"Task {status}." + (f" Reason: {reason}" if reason else ""),
        "last_closed_thread_id": thread_id,
    }
    state.update(updates)
    if hasattr(context.state_manager, "update"):
        await context.state_manager.update(project_id, updates)
    if hasattr(context.state_manager, "flush_to_disk"):
        await context.state_manager.flush_to_disk()
    await context.event_bus.publish(
        "task.closed",
        new_event(
            "task.closed",
            payload={"project_id": project_id, "thread_id": thread_id, "status": status, "reason": reason},
            project_id=project_id,
            thread_id=thread_id,
            correlation_id=project_id,
        ).model_dump(),
    )
    return CommandOutcome(ok=True, message=f"Task {status}: {thread_id}")
