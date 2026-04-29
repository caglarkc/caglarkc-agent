from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from rich.panel import Panel
from rich.table import Table
from textual.widgets import RichLog, Static

from src.interfaces.cli.notifier import Notification


def _seconds_remaining(expires_at: str | None) -> str:
    if not expires_at:
        return "n/a"
    remaining = datetime.fromisoformat(expires_at) - datetime.now(timezone.utc)
    seconds = int(remaining.total_seconds())
    if seconds <= 0:
        return "expired"
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


class SprintStatusPanel(Static):
    def render_from_state(self, state: dict[str, Any] | None) -> Panel:
        table = Table.grid(expand=True)
        table.add_column()
        table.add_column()
        if not state:
            table.add_row("State", "No active project")
        else:
            table.add_row("Project", str(state.get("project_name", "unknown")))
            table.add_row("Sprint", str(state.get("current_sprint", 0)))
            table.add_row("Status", str(state.get("sprint_status", "unknown")))
            table.add_row("Type", str(state.get("sprint_type", "unknown")))
            file_registry = state.get("file_registry", {})
            files = ", ".join(f"{path}:{status}" for path, status in file_registry.items()) or "none"
            table.add_row("Files", files)
        return Panel(table, title="Sprint State", border_style="cyan")

    def update_state(self, state: dict[str, Any] | None) -> None:
        self.update(self.render_from_state(state))


class EventLogPanel(RichLog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, wrap=True, highlight=True, markup=False, **kwargs)

    def push_notification(self, notification: Notification) -> None:
        self.write(f"[{notification.level.upper()}] {notification.message}")


class ApprovalPanel(Static):
    def render_from_state(self, approval: dict[str, Any] | None) -> Panel:
        table = Table.grid(expand=True)
        table.add_column()
        table.add_column()
        if not approval:
            table.add_row("Approval", "No active approval")
        else:
            status = approval.get("status", "pending")
            if _seconds_remaining(approval.get("expires_at")) == "expired":
                status = "expired"
            table.add_row("Approval ID", str(approval.get("approval_id", "unknown")))
            table.add_row("Type", str(approval.get("approval_type", "unknown")))
            table.add_row("Status", status)
            table.add_row("Timeout", _seconds_remaining(approval.get("expires_at")))
        return Panel(table, title="Approval Queue", border_style="yellow")

    def update_approval(self, approval: dict[str, Any] | None) -> None:
        self.update(self.render_from_state(approval))
