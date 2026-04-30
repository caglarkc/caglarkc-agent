from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.config.settings import get_settings
from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.state_manager import StateManager
from src.storage.models import Project
from src.storage.repository import Repository


class FakeGraph:
    def __init__(self) -> None:
        self.state_update = None
        self.invoked = False

    async def aupdate_state(self, config, values, as_node=None):  # noqa: ANN001, ANN202
        self.state_update = values

    async def ainvoke(self, payload, config=None):  # noqa: ANN001, ANN202
        self.invoked = True

    async def aget_state(self, config):  # noqa: ANN001, ANN202
        return SimpleNamespace(values=self.state_update or {}, next=[])


def _configure_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("PROJECTS_ROOT", str(tmp_path / "projects"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "data" / "orchestrator.db"))
    monkeypatch.setenv("GRAPH_CHECKPOINT_PATH", str(tmp_path / "data" / "checkpoints.sqlite"))
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_task_received_prefers_existing_thread_state_over_event_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    bus = EventBus()
    await bus.reset()
    state_manager = StateManager()
    await state_manager.reset()
    repository = Repository()
    await repository.initialize()
    await repository.upsert_project(Project(project_id="project-old", name="demo", description="old", status="active"))
    await repository.upsert_project(Project(project_id="project-new", name="demo", description="new", status="active"))
    await state_manager.set(
        "project-old",
        {
            "project_id": "project-old",
            "project_name": "demo",
            "current_thread_id": "thread-1",
            "planning_thread_id": "thread-1",
            "planning_status": "draft_ready",
            "task_description": "ilk mesaj",
            "conversation_history": [{"role": "user", "content": "ilk mesaj"}],
            "draft_plan": {"summary": "ilk mesaj", "sprint_type": "feature", "files": []},
        },
    )
    graph = FakeGraph()
    manager = GraphManager(event_bus=bus, state_manager=state_manager, repository=repository)
    manager.attach_graph(graph)

    await manager.handle_task_received(
        new_event(
            "task.received",
            payload={"task_description": "ikinci mesaj"},
            project_id="project-new",
            thread_id="thread-1",
        ).model_dump()
    )

    assert graph.invoked is True
    assert graph.state_update["project_id"] == "project-old"
    assert graph.state_update["task_description"] == "ikinci mesaj"
    assert graph.state_update["conversation_history"] == [{"role": "user", "content": "ilk mesaj"}]
    assert graph.state_update["draft_plan"]["summary"] == "ilk mesaj"
