from __future__ import annotations

from pathlib import Path

import pytest

from src.config.settings import get_settings
from src.graph.nodes.executor import executor_node
from src.graph.nodes.validator import validator_node
from src.graph.state import build_initial_state


def _configure_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("PROJECTS_ROOT", str(tmp_path / "projects"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "data" / "orchestrator.db"))
    monkeypatch.setenv("GRAPH_CHECKPOINT_PATH", str(tmp_path / "data" / "checkpoints.sqlite"))
    get_settings.cache_clear()


def _merge(base: dict, updates: dict) -> dict:
    merged = dict(base)
    merged.update(updates)
    return merged


@pytest.mark.asyncio
async def test_executor_passes_valid_python_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _configure_paths(monkeypatch, tmp_path)
    state = build_initial_state(
        project_name="executor-valid",
        task_description="generate valid python",
        project_id="project-executor-valid",
        current_thread_id="thread-executor-valid",
    )
    project_root = get_settings().projects_root / state["project_name"]
    project_root.mkdir(parents=True)
    (project_root / "app.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")
    state["worker_outputs"] = {"worker_a": ["app.py"], "worker_b": [], "worker_c": []}

    result = await executor_node(state)

    assert result["last_execution_status"] == "passed"
    assert result["runtime_errors"] == []
    assert result["execution_results"][0]["check"] == "python_compile"


@pytest.mark.asyncio
async def test_executor_errors_feed_validator_revision_tasks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    state = build_initial_state(
        project_name="executor-invalid",
        task_description="generate invalid python",
        project_id="project-executor-invalid",
        current_thread_id="thread-executor-invalid",
    )
    project_root = get_settings().projects_root / state["project_name"]
    project_root.mkdir(parents=True)
    (project_root / "app.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    state["worker_outputs"] = {"worker_a": ["app.py"], "worker_b": [], "worker_c": []}

    state = _merge(state, await executor_node(state))
    result = await validator_node(state)

    assert state["last_execution_status"] == "failed"
    assert result["validation_issues"][0]["target_file"] == "app.py"
    assert result["revision_tasks"][0]["target_file"] == "app.py"


@pytest.mark.asyncio
async def test_executor_detects_js_dom_id_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    state = build_initial_state(
        project_name="executor-dom-mismatch",
        task_description="restaurant site",
        project_id="project-executor-dom",
        current_thread_id="thread-executor-dom",
    )
    project_root = get_settings().projects_root / state["project_name"]
    project_root.mkdir(parents=True)
    (project_root / "index.html").write_text(
        '<!doctype html><html><body><button id="reserve-btn">Reserve</button><script src="script.js"></script></body></html>',
        encoding="utf-8",
    )
    (project_root / "script.js").write_text(
        "document.getElementById('menu-button').addEventListener('click', () => {});\n",
        encoding="utf-8",
    )
    state["worker_outputs"] = {"worker_a": ["index.html"], "worker_b": [], "worker_c": ["script.js"]}

    state = _merge(state, await executor_node(state))
    result = await validator_node(state)

    assert state["last_execution_status"] == "failed"
    targets = {issue["target_file"] for issue in result["validation_issues"]}
    assert {"index.html", "script.js"}.issubset(targets)
    assert any(issue["code"] == "executor_dom_consistency" for issue in result["validation_issues"])
