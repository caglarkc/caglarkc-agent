from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from src.config.settings import get_settings
from src.core.ai_scanner import ProviderResult
from src.core.project_manager import ProjectManager
from src.interfaces.cli import commands
from src.interfaces.cli.commands import CommandContext, execute_command
from src.interfaces.cli.notifier import CLINotifier


@dataclass
class FakeEventBus:
    events: list[tuple[str, dict]] = field(default_factory=list)

    async def publish(self, event_name: str, payload: dict) -> None:
        self.events.append((event_name, payload))


class FakeStateManager:
    def __init__(self) -> None:
        self.state: dict[str, dict] = {}
        self.updates: list[tuple[str, dict]] = []
        self.sets: list[tuple[str, dict]] = []
        self.flushed = False

    async def snapshot(self):  # noqa: ANN201
        return self.state

    async def update(self, key, updates):  # noqa: ANN001, ANN201
        self.updates.append((key, updates))
        self.state.setdefault(key, {}).update(updates)
        return self.state[key]

    async def set(self, key, value):  # noqa: ANN001, ANN201
        self.sets.append((key, value))
        self.state[key] = dict(value)

    async def get(self, key, default=None):  # noqa: ANN001, ANN201
        return dict(self.state.get(key, default if default is not None else {}))

    async def flush_to_disk(self):  # noqa: ANN201
        self.flushed = True


def _configure_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("PROJECTS_ROOT", str(tmp_path / "projects"))
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "data" / "orchestrator.db"))
    monkeypatch.setenv("GRAPH_CHECKPOINT_PATH", str(tmp_path / "data" / "checkpoints.sqlite"))
    get_settings.cache_clear()


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


@pytest.mark.asyncio
async def test_new_command_creates_named_project_and_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    event_bus = FakeEventBus()
    state_manager = FakeStateManager()
    context = CommandContext(event_bus, None, CLINotifier(), state_manager, None, None)

    outcome = await execute_command("/new CaglarKc NutritionApp", context)

    assert outcome.ok is True
    assert "CaglarKc NutritionApp" in outcome.message
    assert context.current_state is not None
    assert context.current_state["project_name"] == "CaglarKc NutritionApp"
    assert context.current_state["current_thread_id"].startswith("thread-")
    assert state_manager.sets


@pytest.mark.asyncio
async def test_r_command_publishes_message_to_active_project_thread(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    event_bus = FakeEventBus()
    state_manager = FakeStateManager()
    context = CommandContext(event_bus, None, CLINotifier(), state_manager, None, None)
    await execute_command("/new CaglarKc NutritionApp", context)

    outcome = await execute_command("/r kalori takibi olacak", context)

    assert outcome.ok is True
    event_name, payload = event_bus.events[0]
    assert event_name == "task.received"
    assert payload["project_id"] == context.current_state["project_id"]
    assert payload["thread_id"] == context.current_state["current_thread_id"]
    assert payload["payload"]["chat_message"] is True
    assert payload["payload"]["task_description"] == "kalori takibi olacak"


@pytest.mark.asyncio
async def test_plan_command_requests_plan_from_existing_conversation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    event_bus = FakeEventBus()
    state_manager = FakeStateManager()
    context = CommandContext(event_bus, None, CLINotifier(), state_manager, None, None)
    await execute_command("/new CaglarKc NutritionApp", context)
    project_id = context.current_state["project_id"]
    context.current_state["conversation_history"] = [{"role": "user", "content": "kalori takibi olacak"}]
    await state_manager.set(project_id, context.current_state)

    outcome = await execute_command("/plan CaglarKc NutritionApp", context)

    assert outcome.ok is True
    event_name, payload = event_bus.events[0]
    assert event_name == "task.received"
    assert payload["project_id"] == project_id
    assert payload["payload"]["execution_requested"] is True
    assert payload["payload"]["suppress_user_turn"] is True
    assert payload["payload"]["plan_from_conversation"] is True


@pytest.mark.asyncio
async def test_resume_by_project_name_restores_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_paths(monkeypatch, tmp_path)
    event_bus = FakeEventBus()
    state_manager = FakeStateManager()
    context = CommandContext(event_bus, None, CLINotifier(), state_manager, None, None)
    await execute_command("/new CaglarKc NutritionApp", context)
    original_thread = context.current_state["current_thread_id"]
    context.current_state = None

    outcome = await execute_command("/resume CaglarKc NutritionApp", context)

    assert outcome.ok is True
    assert context.current_state["project_name"] == "CaglarKc NutritionApp"
    assert context.current_state["current_thread_id"] == original_thread


@pytest.mark.asyncio
async def test_scan_command_renders_health_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeScanner:
        async def scan_all(self):  # noqa: ANN201
            return [
                ProviderResult(
                    provider="gemini",
                    available=True,
                    model_name="gemini-test",
                    detail="response_ok:pong",
                    latency_ms=321,
                    output_tokens=2,
                    tokens_per_second=6.23,
                    response_preview="pong",
                ),
                ProviderResult(
                    provider="openrouter_primary",
                    available=False,
                    model_name="model-x",
                    detail="api_key_missing",
                ),
            ]

    monkeypatch.setattr(commands, "AIScanner", FakeScanner)
    context = CommandContext(
        event_bus=FakeEventBus(),
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=FakeStateManager(),
        current_state=None,
        active_approval=None,
    )

    outcome = await execute_command("/scan", context)

    assert outcome.ok is True
    assert "✓ gemini  gemini-test  response_ok:pong" in outcome.message
    assert "latency=321ms" in outcome.message
    assert "out_tokens=2" in outcome.message
    assert "tok/s=6.23" in outcome.message
    assert "response='pong'" in outcome.message
    assert "✗ openrouter_primary  model-x  api_key_missing" in outcome.message


@pytest.mark.asyncio
async def test_start_command_approves_pending_plan() -> None:
    event_bus = FakeEventBus()
    state_manager = FakeStateManager()
    state = {
        "project_id": "project-1",
        "project_name": "Demo",
        "current_thread_id": "thread-1",
        "planning_thread_id": "thread-1",
        "planning_status": "awaiting_approval",
        "awaiting_approval": True,
        "approval_request": {"approval_id": "approval-1", "thread_id": "thread-1", "project_id": "project-1"},
    }
    state_manager.state["project-1"] = state
    context = CommandContext(
        event_bus=event_bus,
        graph_manager=None,
        notifier=CLINotifier(),
        state_manager=state_manager,
        current_state=state,
        active_approval=state["approval_request"],
    )

    outcome = await execute_command("/start", context)

    assert outcome.ok is True
    event_name, payload = event_bus.events[0]
    assert event_name == "plan.approved"
    assert payload["payload"]["approval_id"] == "approval-1"


@pytest.mark.asyncio
async def test_recover_command_invokes_graph_manager() -> None:
    state_manager = FakeStateManager()

    class FakeGraphManager:
        async def recover_project_execution(self, project_ref=None):  # noqa: ANN001
            return {
                "ok": True,
                "project_id": "project-1",
                "project_name": project_ref or "active",
                "thread_id": "thread-1",
                "next_node": "dispatcher",
                "actions": ["requeued stale assignment script.js"],
            }

    await state_manager.set("project-1", {"project_id": "project-1", "project_name": "Demo"})
    context = CommandContext(
        event_bus=FakeEventBus(),
        graph_manager=FakeGraphManager(),
        notifier=CLINotifier(),
        state_manager=state_manager,
        current_state={"project_id": "project-1", "project_name": "Demo"},
        active_approval=None,
    )

    outcome = await execute_command("/recover Demo", context)

    assert outcome.ok is True
    assert "next=dispatcher" in outcome.message
