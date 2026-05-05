from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.config.settings import get_settings
from src.core.project_manager import ProjectManager
from src.graph.nodes.reviewer import reviewer_node
from src.graph.state import build_initial_state


@pytest.mark.asyncio
async def test_approved_path_calls_update_plan_snapshot_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Regression: approved branch must not call update_plan_snapshot twice (duplicates plan sprints)."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("PROJECTS_ROOT", str(tmp_path / "projects"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "data" / "orchestrator.db"))
    monkeypatch.setenv("MEMORY_AUTO_ENABLED", "false")
    get_settings.cache_clear()

    snapshot_calls = 0

    async def track_snapshot(
        self: ProjectManager,
        project_name: str,
        *,
        sprint_number: int,
        sprint_type: str,
        status: str,
        files: list[str],
        dependencies: dict[str, list[str]],
        plan_version: int,
        scope_changed: bool = False,
    ) -> Path:
        nonlocal snapshot_calls
        snapshot_calls += 1
        snap_dir = tmp_path / "projects" / project_name / ".meta" / "sprints"
        snap_dir.mkdir(parents=True, exist_ok=True)
        path = snap_dir / f"sprint_{sprint_number:03d}_v{plan_version}.json"
        path.write_text("{}", encoding="utf-8")
        return path

    monkeypatch.setattr(ProjectManager, "update_plan_snapshot", track_snapshot)

    async def no_issues(_state: dict[str, Any]) -> dict[str, Any]:
        return {"issues": []}

    monkeypatch.setattr("src.graph.nodes.reviewer.run_final_project_review", no_issues)

    state = build_initial_state(
        project_name="rp-snap",
        task_description="t",
        project_id="proj-rp-snap",
        current_thread_id="thr-rp-snap",
    )
    state["current_sprint"] = 1
    state["plan_version"] = 1
    state["sprint_type"] = "feature"
    state["file_registry"] = {"app.py": "done"}
    state["worker_queue"] = []
    state["dependencies"] = {"app.py": []}
    state["validation_issues"] = []

    await reviewer_node(state)

    assert snapshot_calls == 1
