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
    def __init__(self) -> None:
        self.updates: list[tuple[str, dict]] = []
        self.flushed = False

    async def snapshot(self):  # noqa: ANN201
        return {}

    async def update(self, key, updates):  # noqa: ANN001, ANN201
        self.updates.append((key, updates))
        return updates

    async def flush_to_disk(self):  # noqa: ANN201
        self.flushed = True


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


@pytest.mark.asyncio
async def test_close_command_closes_active_planning_task() -> None:
    event_bus = FakeEventBus()
    state_manager = FakeStateManager()
    state = {
        "project_id": "project-1",
        "project_name": "demo",
        "current_thread_id": "thread-1",
        "planning_thread_id": "thread-1",
        "planning_status": "draft_ready",
        "awaiting_approval": False,
    }
    context = CommandContext(
        event_bus=event_bus,
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=state_manager,
        current_state=state,
        active_approval=None,
    )

    outcome = await execute_command("/close bitti", context)

    assert outcome.ok is True
    assert state["planning_status"] == "closed"
    assert state_manager.updates[0][0] == "project-1"
    assert state_manager.updates[0][1]["planning_status"] == "closed"
    event_name, payload = event_bus.events[0]
    assert event_name == "task.closed"
    assert payload["payload"]["thread_id"] == "thread-1"


@pytest.mark.asyncio
async def test_reject_without_approval_rejects_active_planning_task() -> None:
    event_bus = FakeEventBus()
    state_manager = FakeStateManager()
    state = {
        "project_id": "project-1",
        "current_thread_id": "thread-1",
        "planning_thread_id": "thread-1",
        "planning_status": "draft_ready",
    }
    context = CommandContext(
        event_bus=event_bus,
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=state_manager,
        current_state=state,
        active_approval=None,
    )

    outcome = await execute_command("/reject gerek yok", context)

    assert outcome.ok is True
    assert state["planning_status"] == "rejected"
    assert event_bus.events[0][0] == "task.closed"
    assert event_bus.events[0][1]["payload"]["status"] == "rejected"


@pytest.mark.asyncio
async def test_task_after_closed_state_gets_new_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_active_project(self):  # noqa: ANN001, ANN202
        return None

    monkeypatch.setattr(ProjectManager, "active_project", fake_active_project)
    event_bus = FakeEventBus()
    state = {
        "project_id": "project-1",
        "current_thread_id": "thread-old",
        "planning_thread_id": "thread-old",
        "planning_status": "closed",
        "conversation_history": [{"role": "user", "content": "old"}],
    }
    context = CommandContext(
        event_bus=event_bus,
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=FakeStateManager(),
        current_state=state,
        active_approval=None,
    )

    outcome = await execute_command("/task yeni is", context)

    assert outcome.ok is True
    assert state["current_thread_id"].startswith("thread-")
    assert state["current_thread_id"] != "thread-old"
    assert state["conversation_history"] == []
    assert event_bus.events[0][1]["thread_id"] == state["current_thread_id"]
