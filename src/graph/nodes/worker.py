from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from src.core.event_bus import EventBus
from src.core.project_manager import ProjectManager
from src.storage.models import FileRecord
from src.storage.repository import Repository


async def worker_node(state: dict) -> dict:
    repository = Repository()
    project_manager = ProjectManager()
    await repository.initialize()

    queue = deepcopy(state.get("worker_queue", []))
    registry = deepcopy(state.get("file_registry", {}))
    outputs = deepcopy(state.get("worker_outputs", {}))
    job = next((item for item in queue if item.get("status", "planned") != "done"), None)

    if job is None:
        return {
            "worker_status": {"worker_stub": "idle"},
            "messages": [*state.get("messages", []), "worker found no pending jobs"],
        }

    file_path = job["file"]
    file_content = (
        "# Phase 1 Smoke Artifact\n\n"
        f"Project: {state['project_name']}\n"
        f"Task: {state['task_description']}\n"
        "Result: planner -> worker -> reviewer completed.\n"
    )
    await project_manager.write_project_file(state["project_name"], file_path, file_content)

    job["status"] = "done"
    registry[file_path] = "done"
    outputs.setdefault("worker_stub", []).append(file_path)

    await repository.create_file_record(
        FileRecord(
            file_id=str(uuid4()),
            project_id=state["project_id"],
            path=file_path,
            status="done",
            worker_id="worker_stub",
        )
    )
    await EventBus().emit(
        "sprint.worker_done",
        {"worker_id": "worker_stub", "file": file_path, "project_id": state["project_id"]},
    )

    return {
        "worker_queue": queue,
        "file_registry": registry,
        "worker_outputs": outputs,
        "worker_status": {"worker_stub": "done"},
        "messages": [*state.get("messages", []), "worker completed"],
    }
