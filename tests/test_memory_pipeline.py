from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from src.config.settings import get_settings
from src.core.memory_pipeline import MemoryReviewContext, _run_memory_pipeline, schedule_memory_pipeline_after_review


@pytest.fixture
def projects_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("PROJECTS_ROOT", str(tmp_path))
    monkeypatch.setenv("MEMORY_MIN_HOURS_BETWEEN_RUNS", "0")
    monkeypatch.setenv("MEMORY_MIN_SESSIONS", "1")
    monkeypatch.setenv("MEMORY_SESSION_SCAN_INTERVAL_SECONDS", "0")
    monkeypatch.setenv("MEMORY_CONSOLIDATION_ENABLED", "true")
    monkeypatch.setenv("MEMORY_CONSOLIDATION_USE_LLM", "false")
    monkeypatch.setenv("MEMORY_AUTO_ENABLED", "true")
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_pipeline_writes_extract_and_planner_memory(projects_root: Path) -> None:
    root = projects_root / "Alpha"
    (root / ".meta" / "sprints").mkdir(parents=True, parents=True)
    (root / ".meta" / "sprints" / "sprint_001_v1.json").write_text("{}", encoding="utf-8")

    ctx = MemoryReviewContext(
        project_id="proj-test",
        project_name="Alpha",
        thread_id="thread-1",
        current_sprint=2,
        sprint_status="approved",
        reviewer_decision="approved",
        file_registry={"src/app.py": "done"},
        dependencies={"src/app.py": []},
        plan_version=1,
    )
    await _run_memory_pipeline(ctx)

    memory_root = root / ".meta" / "memory"
    extracts = list((memory_root / "extracts").glob("*.md"))
    assert extracts
    planner = memory_root / "planner_memory.md"
    assert planner.exists()
    assert "Planner memory" in planner.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_pipeline_skipped_when_min_sessions_not_met(projects_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEMORY_MIN_SESSIONS", "5")
    get_settings.cache_clear()

    root = projects_root / "Beta"
    (root / ".meta" / "sprints").mkdir(parents=True, parents=True)
    (root / ".meta" / "sprints" / "sprint_001_v1.json").write_text("{}", encoding="utf-8")

    ctx = MemoryReviewContext(
        project_id="proj-beta",
        project_name="Beta",
        thread_id="thread-1",
        current_sprint=2,
        sprint_status="approved",
        reviewer_decision="approved",
        file_registry={},
        dependencies={},
        plan_version=1,
    )
    await _run_memory_pipeline(ctx)

    planner = root / ".meta" / "memory" / "planner_memory.md"
    assert not planner.exists()


@pytest.mark.asyncio
async def test_schedule_dedupes_concurrent_requests(projects_root: Path) -> None:
    root = projects_root / "Gamma"
    (root / ".meta" / "sprints").mkdir(parents=True, parents=True)
    (root / ".meta" / "sprints" / "sprint_001_v1.json").write_text("{}", encoding="utf-8")

    ctx = MemoryReviewContext(
        project_id="proj-gamma",
        project_name="Gamma",
        thread_id="thread-1",
        current_sprint=2,
        sprint_status="approved",
        reviewer_decision="approved",
        file_registry={"f.py": "done"},
        dependencies={},
        plan_version=1,
    )
    await asyncio.gather(schedule_memory_pipeline_after_review(ctx), schedule_memory_pipeline_after_review(ctx))
    from src.core import memory_pipeline as mp

    pending = mp._TASKS.get("proj-gamma")
    if pending:
        await asyncio.wait_for(pending, timeout=5.0)

    extracts = list((root / ".meta" / "memory" / "extracts").glob("*.md"))
    assert len(extracts) == 1
