from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _age_text(timestamp: str | None) -> str:
    if not timestamp:
        return "never"
    delta = datetime.now(timezone.utc) - datetime.fromisoformat(timestamp)
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    minutes = seconds // 60
    return f"{minutes}m ago"


def format_status_summary(state: dict[str, Any] | None, *, active_approval: dict[str, Any] | None = None) -> str:
    if not state:
        return "No active project state."
    queue = state.get("worker_queue", [])
    worker_status = state.get("worker_status", {})
    stalled = state.get("stalled_since")
    lines = [
        f"Project: {state.get('project_name', 'unknown')}",
        f"Sprint: {state.get('current_sprint', 0)} | Type: {state.get('sprint_type', 'unknown')} | Status: {state.get('sprint_status', 'unknown')}",
        f"Queue: {len(queue)} | Active Assignment: {bool(state.get('active_assignment'))}",
        "Workers: " + (", ".join(f"{worker}={status}" for worker, status in worker_status.items()) or "none"),
        f"Last Heartbeat: {_age_text(state.get('last_heartbeat_at'))}",
        f"Stalled: {'yes' if stalled else 'no'}",
    ]
    if active_approval:
        lines.append(
            f"Approval: {active_approval.get('approval_id')} | Type: {active_approval.get('approval_type')} | Status: {active_approval.get('status')}"
        )
    return "\n".join(lines)


def format_projects_listing(projects: list[Any], *, active_project_id: str | None = None) -> str:
    if not projects:
        return "Projects: none"
    lines = ["Projects:"]
    for project in projects:
        marker = "*" if getattr(project, "project_id", None) == active_project_id or project.metadata.get("selected") else "-"
        lines.append(f"{marker} {project.project_id} | {project.name} | {project.status}")
    return "\n".join(lines)


def format_project_history(project_name: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return f"History: {project_name} | none"
    lines = [f"History: {project_name}"]
    for item in items:
        lines.append(
            f"- sprint {item['number']} | {item['type']} | {item['status']} | review={item['review_cycles']} | v{item['plan_version']}"
        )
    return "\n".join(lines)
