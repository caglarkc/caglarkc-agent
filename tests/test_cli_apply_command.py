from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from src.core.project_manager import ProjectManager
from src.interfaces.cli.commands import CommandContext, execute_command
from src.interfaces.cli.notifier import CLINotifier


@dataclass
class FakeEventBus:
    events: list[tuple[str, dict]] = field(default_factory=list)

    async def publish(self, event_name: str, payload: dict) -> None:
        self.events.append((event_name, payload))


class FakeStateManager:
    async def snapshot(self):  # noqa: ANN201
        return {}


@pytest.mark.asyncio
async def test_apply_command_sets_execution_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_active_project(self):  # noqa: ANN001, ANN202
        return None

    monkeypatch.setattr(ProjectManager, "active_project", fake_active_project)
    event_bus = FakeEventBus()
    context = CommandContext(
        event_bus=event_bus,
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=FakeStateManager(),
        current_state={"project_id": "project-1", "current_thread_id": "thread-1", "task_description": "site kur"},
        active_approval=None,
    )

    outcome = await execute_command("/apply", context)

    assert outcome.ok is True
    assert event_bus.events
    event_name, payload = event_bus.events[0]
    assert event_name == "task.received"
    assert payload["payload"]["execution_requested"] is True
    assert payload["payload"]["suppress_user_turn"] is True
    assert payload["thread_id"] == "thread-1"
    assert payload["payload"]["task_id"] == "thread-1"


@pytest.mark.asyncio
async def test_task_command_returns_and_publishes_stable_thread_id(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_active_project(self):  # noqa: ANN001, ANN202
        return None

    monkeypatch.setattr(ProjectManager, "active_project", fake_active_project)
    event_bus = FakeEventBus()
    state = {"project_id": "project-1"}
    context = CommandContext(
        event_bus=event_bus,
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=FakeStateManager(),
        current_state=state,
        active_approval=None,
    )

    outcome = await execute_command("/task site kur", context)

    assert outcome.ok is True
    assert state["current_thread_id"].startswith("thread-")
    assert state["planning_thread_id"] == state["current_thread_id"]
    assert state["current_thread_id"] in outcome.message
    event_name, payload = event_bus.events[0]
    assert event_name == "task.received"
    assert payload["thread_id"] == state["current_thread_id"]
    assert payload["payload"]["task_id"] == state["current_thread_id"]
