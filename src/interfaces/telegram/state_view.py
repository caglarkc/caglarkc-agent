from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _age_text(timestamp: str | None) -> str:
    if not timestamp:
        return "never"
    delta = datetime.now(timezone.utc) - datetime.fromisoformat(timestamp)
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}m"


def format_telegram_status(state: dict[str, Any] | None, *, active_approval: dict[str, Any] | None = None) -> str:
    if not state:
        return "Durum: aktif proje yok"
    queue = state.get("worker_queue", [])
    workers = state.get("worker_status", {})
    worker_text = ", ".join(f"{worker}:{status}" for worker, status in workers.items()) or "none"
    lines = [
        f"Proje: {state.get('project_name', 'unknown')}",
        f"Sprint: {state.get('current_sprint', 0)} | {state.get('sprint_type', 'unknown')} | {state.get('sprint_status', 'unknown')}",
        f"Planning: {state.get('planning_status', 'unknown')}",
        f"Queue: {len(queue)} | Workers: {worker_text}",
        f"Heartbeat: {_age_text(state.get('last_heartbeat_at'))} | Stalled: {'yes' if state.get('stalled_since') else 'no'}",
    ]
    if active_approval:
        lines.append(
            f"Approval: {active_approval.get('approval_id')} | {active_approval.get('approval_type')} | {active_approval.get('status', 'pending')}"
        )
    manager_reply = str(state.get("manager_reply", "") or "")
    if manager_reply:
        lines.append(f"Manager: {manager_reply[:180]}")
    return "\n".join(lines)


def format_telegram_projects(projects: list[Any], *, active_project_id: str | None = None) -> str:
    if not projects:
        return "Projeler: yok"
    lines = ["Projeler:"]
    for project in projects:
        marker = "*" if getattr(project, "project_id", None) == active_project_id or project.metadata.get("selected") else "-"
        lines.append(f"{marker} {project.project_id} | {project.name} | {project.status}")
    return "\n".join(lines)


def format_telegram_history(project_name: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return f"Gecmis: {project_name} | yok"
    lines = [f"Gecmis: {project_name}"]
    for item in items:
        lines.append(f"- S{item['number']} | {item['type']} | {item['status']} | r={item['review_cycles']} | v{item['plan_version']}")
    return "\n".join(lines)
