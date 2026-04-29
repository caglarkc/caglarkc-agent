from __future__ import annotations

from pathlib import Path

import pytest

from src.config.settings import get_settings
from src.core.event_bus import EventBus
from src.graph.nodes.planner import planner_node
from src.graph.state import build_initial_state


def _configure_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MANAGER_USE_GEMINI", "0")
    monkeypatch.setenv("USE_LEGACY_PLANNER", "0")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("PROJECTS_ROOT", str(tmp_path / "projects"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "data" / "orchestrator.db"))
    monkeypatch.setenv("GRAPH_CHECKPOINT_PATH", str(tmp_path / "data" / "checkpoints.sqlite"))
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_planner_node_keeps_discussion_mode_without_queue(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    await EventBus().reset()
    state = build_initial_state(
        project_name="demo-project",
        task_description="site kur",
        project_id="project-1",
        current_thread_id="thread-1",
    )

    result = await planner_node(state)

    assert result["worker_queue"] == []
    assert result["awaiting_approval"] is False
    assert result["draft_plan"] is not None
    assert result["planning_status"] in {"needs_input", "draft_ready"}
    assert result["manager_reply"]


@pytest.mark.asyncio
async def test_planner_node_builds_queue_when_execution_is_requested(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    await EventBus().reset()
    state = build_initial_state(
        project_name="demo-project",
        task_description="site kur",
        project_id="project-2",
        current_thread_id="thread-2",
    )
    state["execution_requested"] = True

    result = await planner_node(state)

    assert result["awaiting_approval"] is True
    assert result["approval_request"]["metadata"]["source"] == "gemini_manager"
    assert [item["assignment"]["target_file"] for item in result["worker_queue"]] == [
        "app.py",
        "templates/index.html",
        "static/styles.css",
    ]
    assert result["dependencies"]["templates/index.html"] == ["app.py"]
