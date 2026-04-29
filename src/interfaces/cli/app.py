from __future__ import annotations

from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Input

from src.core.event_bus import EventBus
from src.core.state_manager import StateManager
from src.interfaces.cli.commands import CommandContext, execute_command
from src.interfaces.cli.notifier import CLINotifier
from src.interfaces.cli.panels import ApprovalPanel, EventLogPanel, SprintStatusPanel


EVENT_NAMES = [
    "plan.generated",
    "plan.approval_needed",
    "sprint.started",
    "sprint.worker_done",
    "sprint.review_started",
    "sprint.revision_needed",
    "sprint.completed",
    "system.heartbeat",
    "system.stalled",
    "error.occurred",
]


class OrchestratorCLIApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }
    #body {
        height: 1fr;
        layout: horizontal;
    }
    #left {
        width: 1fr;
    }
    #right {
        width: 1fr;
    }
    #bottom {
        height: 10;
    }
    #command-input {
        dock: bottom;
    }
    """

    BINDINGS = [("ctrl+c", "quit", "Quit")]

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        state_manager: StateManager | None = None,
        graph_manager: Any | None = None,
        notifier: CLINotifier | None = None,
    ) -> None:
        super().__init__()
        self.event_bus = event_bus or EventBus()
        self.state_manager = state_manager or StateManager()
        self.graph_manager = graph_manager
        self.notifier = notifier or CLINotifier()
        self.current_state: dict[str, Any] | None = None
        self.active_approval: dict[str, Any] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="left"):
                yield SprintStatusPanel(id="sprint-panel")
            with Vertical(id="right"):
                yield EventLogPanel(id="event-log")
        yield ApprovalPanel(id="approval-panel")
        yield Input(placeholder="Enter command, /help for options", id="command-input")
        yield Footer()

    async def on_mount(self) -> None:
        await self._hydrate_from_state_manager()
        await self._subscribe_events()
        self.refresh_panels()
        self.set_interval(1.0, self.refresh_approval_panel)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        outcome = await execute_command(
            event.value,
            self._command_context(),
        )
        self._log_notification(getattr(self.notifier, outcome.level)(outcome.message))
        event.input.value = ""

    async def _hydrate_from_state_manager(self) -> None:
        snapshot = await self.state_manager.snapshot()
        if snapshot:
            _, state = next(reversed(snapshot.items()))
            if isinstance(state, dict):
                self.current_state = state
                approval_request = state.get("approval_request")
                self.active_approval = approval_request if isinstance(approval_request, dict) else None

    async def _subscribe_events(self) -> None:
        for event_name in EVENT_NAMES:
            await self.event_bus.subscribe(event_name, self._handle_event)

    async def _handle_event(self, payload: dict[str, Any] | None) -> None:
        event_type = payload.get("event_type") if isinstance(payload, dict) else "unknown"
        self._log_notification(self.notifier.from_event(event_type, payload if isinstance(payload, dict) else {}))
        if not isinstance(payload, dict):
            return
        if event_type == "plan.approval_needed":
            approval = payload.get("payload", {})
            self.active_approval = approval
            if self.current_state is not None:
                self.current_state["approval_request"] = approval
        elif event_type in {"plan.approved", "plan.rejected", "plan.cancelled"} and self.active_approval:
            self.active_approval["status"] = event_type.split(".")[1]
        else:
            self._merge_state_from_event(payload)
        self.refresh_panels()

    def _merge_state_from_event(self, payload: dict[str, Any]) -> None:
        if self.current_state is None:
            self.current_state = {}
        event_type = payload.get("event_type")
        body = payload.get("payload", {})
        if event_type == "sprint.worker_done":
            target_file = body.get("target_file")
            if target_file:
                self.current_state.setdefault("file_registry", {})[target_file] = "done"
        elif event_type == "sprint.completed":
            result = body.get("result", "approved")
            self.current_state["sprint_status"] = result
        elif event_type == "system.heartbeat":
            self.current_state["last_heartbeat_at"] = payload.get("timestamp")
        elif event_type == "system.stalled":
            self.current_state["stalled_since"] = payload.get("timestamp")

    def refresh_panels(self) -> None:
        self.query_one("#sprint-panel", SprintStatusPanel).update_state(self.current_state)
        self.refresh_approval_panel()

    def refresh_approval_panel(self) -> None:
        self.query_one("#approval-panel", ApprovalPanel).update_approval(self.active_approval)

    def _log_notification(self, notification) -> None:
        self.query_one("#event-log", EventLogPanel).push_notification(notification)

    def _command_context(self) -> CommandContext:
        return CommandContext(
            event_bus=self.event_bus,
            graph_manager=self.graph_manager,
            notifier=self.notifier,
            state_manager=self.state_manager,
            current_state=self.current_state,
            active_approval=self.active_approval,
        )
