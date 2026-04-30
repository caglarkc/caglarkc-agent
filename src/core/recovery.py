from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import aiofiles.ospath


async def analyze_execution_recovery(state: dict[str, Any], project_root: Path) -> tuple[dict[str, Any], str, list[str]]:
    queue = deepcopy(state.get("worker_queue", []))
    file_registry = deepcopy(state.get("file_registry", {}))
    worker_status = {worker_id: "idle" for worker_id in state.get("worker_status", {"worker_a": "idle", "worker_b": "idle", "worker_c": "idle"})}
    worker_outputs = deepcopy(state.get("worker_outputs", {"worker_a": [], "worker_b": [], "worker_c": []}))
    active_assignment = state.get("active_assignment")
    recovery_actions: list[str] = []

    active_target = active_assignment.get("target_file") if isinstance(active_assignment, dict) else None
    for item in queue:
        assignment = item.get("assignment", {})
        target_file = assignment.get("target_file")
        status = item.get("status")
        if status in {"assigned", "in_progress"} or (target_file and target_file == active_target):
            item["status"] = "planned"
            item["validation_error"] = item.get("validation_error") or "Recovered stale in-progress assignment."
            if target_file:
                file_registry[target_file] = "planned"
                recovery_actions.append(f"requeued stale assignment {target_file}")

    for target_file, status in list(file_registry.items()):
        if status in {"reserved", "in_progress"}:
            file_registry[target_file] = "planned"
            recovery_actions.append(f"released stale file reservation {target_file}")

    for target_file, status in list(file_registry.items()):
        path = (project_root / target_file).resolve()
        try:
            path.relative_to(project_root.resolve())
        except ValueError:
            file_registry[target_file] = "planned"
            recovery_actions.append(f"reset unsafe file path {target_file}")
            continue
        exists = await aiofiles.ospath.exists(path)
        if status == "done" and not exists:
            file_registry[target_file] = "planned"
            for item in queue:
                if item.get("assignment", {}).get("target_file") == target_file:
                    item["status"] = "planned"
                    item["validation_error"] = "Recovered missing output file."
            for outputs in worker_outputs.values():
                while target_file in outputs:
                    outputs.remove(target_file)
            recovery_actions.append(f"requeued missing done file {target_file}")

    for item in queue:
        target_file = item.get("assignment", {}).get("target_file")
        if not target_file:
            continue
        if file_registry.get(target_file) == "planned" and item.get("status") == "done":
            item["status"] = "planned"
            recovery_actions.append(f"aligned queue status for {target_file}")
        elif file_registry.get(target_file) == "done" and item.get("status") in {"planned", "assigned", "in_progress"}:
            path = (project_root / target_file).resolve()
            if await aiofiles.ospath.exists(path):
                item["status"] = "done"
                recovery_actions.append(f"accepted existing done file {target_file}")

    has_planned = any(item.get("status") == "planned" for item in queue)
    all_done = bool(file_registry) and all(status == "done" for status in file_registry.values())
    next_node = "executor" if all_done else "dispatcher"
    recovered_status = "active" if has_planned else state.get("sprint_status", "active")
    updates = {
        "worker_queue": queue,
        "file_registry": file_registry,
        "worker_status": worker_status,
        "worker_outputs": worker_outputs,
        "active_assignment": None,
        "active_assignments": {},
        "awaiting_approval": False if state.get("planning_status") == "approved_for_execution" else state.get("awaiting_approval", False),
        "planning_status": "approved_for_execution" if state.get("worker_queue") else state.get("planning_status", "chat_ready"),
        "sprint_status": recovered_status,
        "stalled_since": None,
        "messages": ["recovery prepared execution resume"],
    }
    return updates, next_node, recovery_actions
