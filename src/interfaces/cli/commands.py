from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.core.contracts import new_event
from src.interfaces.cli.notifier import CLINotifier
from src.interfaces.cli.state_view import format_status_summary


HELP_TEXT = "\n".join(
    [
        "/task <metin>",
        "/status",
        "/approve [approval_id]",
        "/reject [approval_id] [reason]",
        "/cancel [approval_id] [reason]",
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
    if command.name == "task":
        if not command.args:
            return CommandOutcome(ok=False, message="Usage: /task <metin>", level="error")
        task_text = " ".join(command.args)
        state = context.current_state or {}
        await context.event_bus.publish(
            "task.received",
            new_event(
                "task.received",
                payload={"task_description": task_text},
                project_id=state.get("project_id"),
                thread_id=state.get("current_thread_id"),
                correlation_id=state.get("project_id"),
            ).model_dump(),
        )
        return CommandOutcome(ok=True, message=f"Task queued: {task_text}")
    if command.name == "status":
        return CommandOutcome(
            ok=True,
            message=format_status_summary(context.current_state, active_approval=context.active_approval),
        )
    if command.name in {"approve", "reject", "cancel"}:
        return await _handle_approval_command(command, context)
    return CommandOutcome(ok=False, message=f"Unknown command: /{command.name}\n{HELP_TEXT}", level="error")


async def _handle_approval_command(command: ParsedCommand, context: CommandContext) -> CommandOutcome:
    active = context.active_approval
    approval_id: str | None = command.args[0] if command.args else None
    reason = " ".join(command.args[1:]) if len(command.args) > 1 else ""
    if approval_id is None and active is not None:
        approval_id = active.get("approval_id")
    if not approval_id:
        return CommandOutcome(ok=False, message="No active approval found.", level="warning")

    guard = context.graph_manager.approval_guard if context.graph_manager is not None else None
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
