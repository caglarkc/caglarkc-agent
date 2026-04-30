from __future__ import annotations

from pathlib import Path

import pytest

from src.core.recovery import analyze_execution_recovery
from src.graph.state import build_initial_state


def _entry(state: dict, target_file: str, status: str, worker_id: str = "worker_a") -> dict:
    return {
        "assignment": {
            "task_id": f"task-{target_file}",
            "project_id": state["project_id"],
            "thread_id": state["current_thread_id"],
            "worker_id": worker_id,
            "target_file": target_file,
            "description": f"Generate {target_file}",
            "sprint_id": "sprint-1",
            "correlation_id": state["project_id"],
            "metadata": {"task_type": target_file},
        },
        "status": status,
        "validation_error": None,
        "retry_count": 0,
        "blocked_by": [],
        "task_type": target_file,
    }


@pytest.mark.asyncio
async def test_recovery_requeues_stale_in_progress_assignment(tmp_path: Path) -> None:
    state = build_initial_state(
        project_name="recover-half",
        task_description="recover",
        project_id="project-recover-half",
        current_thread_id="thread-recover-half",
    )
    state.update(
        {
            "worker_queue": [_entry(state, "script.js", "in_progress")],
            "file_registry": {"script.js": "in_progress"},
            "worker_status": {"worker_a": "working", "worker_b": "idle", "worker_c": "idle"},
            "active_assignment": _entry(state, "script.js", "in_progress")["assignment"],
            "planning_status": "approved_for_execution",
        }
    )
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "script.js").write_text("console.log('partial')", encoding="utf-8")

    updates, next_node, actions = await analyze_execution_recovery(state, project_root)

    assert updates["worker_queue"][0]["status"] == "planned"
    assert updates["file_registry"]["script.js"] == "planned"
    assert updates["worker_status"] == {"worker_a": "idle", "worker_b": "idle", "worker_c": "idle"}
    assert updates["active_assignment"] is None
    assert next_node == "dispatcher"
    assert any("script.js" in action for action in actions)


@pytest.mark.asyncio
async def test_recovery_requeues_missing_done_file(tmp_path: Path) -> None:
    state = build_initial_state(
        project_name="recover-missing",
        task_description="recover",
        project_id="project-recover-missing",
        current_thread_id="thread-recover-missing",
    )
    state.update(
        {
            "worker_queue": [_entry(state, "index.html", "done")],
            "file_registry": {"index.html": "done"},
            "worker_outputs": {"worker_a": ["index.html"], "worker_b": [], "worker_c": []},
            "planning_status": "approved_for_execution",
        }
    )

    updates, next_node, actions = await analyze_execution_recovery(state, tmp_path)

    assert updates["worker_queue"][0]["status"] == "planned"
    assert updates["file_registry"]["index.html"] == "planned"
    assert updates["worker_outputs"]["worker_a"] == []
    assert next_node == "dispatcher"
    assert actions == ["requeued missing done file index.html", "aligned queue status for index.html"]
