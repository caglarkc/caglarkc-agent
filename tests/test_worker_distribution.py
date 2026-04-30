from __future__ import annotations

from pathlib import Path

import pytest

from src.config.settings import get_settings
from src.graph.nodes.dispatcher import dispatcher_node
from src.graph.nodes.worker import worker_node
from src.graph.state import build_initial_state


def _configure_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("PROJECTS_ROOT", str(tmp_path / "projects"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "data" / "orchestrator.db"))
    monkeypatch.setenv("GRAPH_CHECKPOINT_PATH", str(tmp_path / "data" / "checkpoints.sqlite"))
    monkeypatch.setenv("WORKER_USE_STUB", "1")
    get_settings.cache_clear()


def _merge(base: dict, updates: dict) -> dict:
    merged = dict(base)
    merged.update(updates)
    return merged


def _queue_entry(state: dict, task_id: str, target_file: str, *, simulate_error: str | None = None) -> dict:
    metadata = {"task_type": target_file}
    if simulate_error:
        metadata["simulate_error"] = simulate_error
    return {
        "assignment": {
            "task_id": task_id,
            "project_id": state["project_id"],
            "thread_id": state["current_thread_id"],
            "worker_id": "unassigned",
            "target_file": target_file,
            "description": f"Generate {target_file}",
            "sprint_id": "sprint-1",
            "correlation_id": state["project_id"],
            "metadata": metadata,
        },
        "status": "planned",
        "validation_error": None,
        "retry_count": 0,
        "blocked_by": [],
        "task_type": target_file,
    }


@pytest.mark.asyncio
async def test_dispatcher_distributes_independent_files_across_three_workers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    state = build_initial_state(
        project_name="worker-distribution",
        task_description="three independent files",
        current_thread_id="thread-dist",
    )
    files = ["a.py", "b.py", "c.py"]
    state.update(
        {
            "dependencies": {path: [] for path in files},
            "file_registry": {path: "planned" for path in files},
            "worker_queue": [_queue_entry(state, f"task-{index}", path) for index, path in enumerate(files)],
        }
    )

    assigned_workers = []
    for _ in files:
        state = _merge(state, await dispatcher_node(state))
        assigned_workers.append(state["active_assignment"]["worker_id"])
        state = _merge(state, await worker_node(state))

    assert assigned_workers == ["worker_a", "worker_b", "worker_c"]
    assert state["file_registry"] == {"a.py": "done", "b.py": "done", "c.py": "done"}


@pytest.mark.asyncio
async def test_retryable_failure_reassigns_to_another_worker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    state = build_initial_state(
        project_name="worker-fallback",
        task_description="retryable fallback",
        current_thread_id="thread-fallback",
    )
    state.update(
        {
            "dependencies": {"fragile.py": []},
            "file_registry": {"fragile.py": "planned"},
            "worker_queue": [_queue_entry(state, "fragile-task", "fragile.py", simulate_error="retryable")],
        }
    )

    state = _merge(state, await dispatcher_node(state))
    first_worker = state["active_assignment"]["worker_id"]
    state = _merge(state, await worker_node(state))
    reassigned_worker = state["worker_queue"][0]["assignment"]["worker_id"]

    assert first_worker == "worker_a"
    assert reassigned_worker == "worker_b"
    assert state["worker_queue"][0]["status"] == "planned"
