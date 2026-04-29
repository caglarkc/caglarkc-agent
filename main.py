from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import os
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os
import httpx

from src.config.logging_config import configure_logging
from src.config.settings import get_settings
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.retry_policy import RetryPolicy
from src.core.state_manager import StateManager
from src.interfaces.cli.app import OrchestratorCLIApp
from src.interfaces.telegram.bot import OrchestratorTelegramBot
from src.storage.repository import Repository


LOGGER = logging.getLogger(__name__)


@dataclass
class OllamaGateResult:
    status: str
    detail: str
    attempts: int


class CLIService:
    def __init__(self, app: OrchestratorCLIApp | None = None) -> None:
        self.app = app or OrchestratorCLIApp()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        run_async = getattr(self.app, "run_async", None)
        if run_async is None:
            return
        self._task = asyncio.create_task(run_async())

    async def shutdown(self) -> None:
        if hasattr(self.app, "exit"):
            self.app.exit()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task


class NullService:
    async def start(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None


class OrchestratorDaemon:
    def __init__(
        self,
        *,
        enable_cli: bool = False,
        enable_telegram: bool = True,
        event_bus: EventBus | None = None,
        state_manager: StateManager | None = None,
        repository: Repository | None = None,
        graph_manager: GraphManager | None = None,
        telegram_bot: OrchestratorTelegramBot | None = None,
        cli_service: Any | None = None,
        ollama_probe: Any | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.settings = get_settings()
        self.enable_cli = enable_cli
        self.enable_telegram = enable_telegram
        self.event_bus = event_bus or EventBus()
        self.state_manager = state_manager or StateManager()
        self.repository = repository or Repository()
        self.graph_manager = graph_manager or GraphManager(
            event_bus=self.event_bus,
            state_manager=self.state_manager,
            repository=self.repository,
        )
        self.telegram_bot = telegram_bot or OrchestratorTelegramBot(
            event_bus=self.event_bus,
            state_manager=self.state_manager,
            graph_manager=self.graph_manager,
        )
        self.cli_service = cli_service or CLIService(
            OrchestratorCLIApp(
                event_bus=self.event_bus,
                state_manager=self.state_manager,
                graph_manager=self.graph_manager,
            )
        )
        self.ollama_probe = ollama_probe or self._default_ollama_probe
        self.retry_policy = retry_policy or RetryPolicy(seed=7)
        self.shutdown_event = asyncio.Event()
        self._shutdown_started = False
        self._last_health: dict[str, Any] = {}

    async def start(self) -> dict[str, Any]:
        await aiofiles.os.makedirs(self.settings.data_dir, exist_ok=True)
        configure_logging(daemon_mode=True)
        await self._write_pid_file()
        await self._restore_state_snapshot()
        await self._subscribe_health_events()
        await self.graph_manager.start()
        await self.repository.initialize()

        gate = await self.run_ollama_gate()
        await self.graph_manager.bootstrap_runtime()
        recovery = await self.graph_manager.recover_pending_threads()

        await self._write_status(
            lifecycle="running",
            detail="daemon_started",
            ollama=gate.__dict__,
            recovery=recovery,
        )

        tasks = []
        if self.enable_telegram and self.settings.telegram_bot_token:
            tasks.append(self.telegram_bot.start())
        if self.enable_cli:
            tasks.append(self.cli_service.start())
        if tasks:
            await asyncio.gather(*tasks)

        LOGGER.info("Daemon startup completed. cli=%s telegram=%s", self.enable_cli, self.enable_telegram)
        return {"ollama": gate.__dict__, "recovery": recovery}

    async def wait_forever(self) -> None:
        await self.shutdown_event.wait()

    async def shutdown(self, reason: str = "shutdown_requested") -> None:
        if self._shutdown_started:
            return
        self._shutdown_started = True
        LOGGER.info("Daemon shutdown requested: %s", reason)
        await self._write_status(lifecycle="stopping", detail=reason)
        tasks = []
        if self.enable_telegram and self.settings.telegram_bot_token:
            tasks.append(self.telegram_bot.shutdown())
        if self.enable_cli:
            tasks.append(self.cli_service.shutdown())
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self.state_manager.flush_to_disk()
        await self.graph_manager.shutdown_runtime()
        await self._write_status(lifecycle="stopped", detail=reason)
        await self._remove_pid_file()
        self.shutdown_event.set()

    async def trigger_signal_shutdown(self, signame: str) -> None:
        await self.shutdown(reason=f"signal:{signame}")

    def install_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.trigger_signal_shutdown(s.name)))
            except NotImplementedError:
                LOGGER.warning("Signal handlers are not available on this platform.")

    async def run_ollama_gate(self, *, max_attempts: int = 3) -> OllamaGateResult:
        last_error = "unreachable"
        for attempt in range(1, max_attempts + 1):
            try:
                result = await self.ollama_probe()
                LOGGER.info("Ollama health gate passed on attempt %s: %s", attempt, result.detail)
                return result
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                LOGGER.warning("Ollama health attempt %s/%s failed: %s", attempt, max_attempts, exc)
                if attempt < max_attempts:
                    await self.retry_policy.sleep(attempt)

        remote_available = bool(
            self.settings.gemini_api_key
            or self.settings.openrouter_api_key_primary
            or self.settings.openrouter_api_key_secondary
        )
        if remote_available:
            result = OllamaGateResult(
                status="degraded",
                detail=f"ollama_unavailable: {last_error}; remote provider fallback enabled",
                attempts=max_attempts,
            )
            LOGGER.warning("Daemon entering degraded mode: %s", result.detail)
            return result
        raise RuntimeError(f"ollama health gate failed after {max_attempts} attempts: {last_error}")

    async def _default_ollama_probe(self) -> OllamaGateResult:
        timeout = httpx.Timeout(self.settings.http_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{self.settings.ollama_base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
        models = payload.get("models", [])
        names = {item.get("model") for item in models if isinstance(item, dict)}
        if self.settings.ollama_model not in names:
            raise RuntimeError(f"configured Ollama model missing: {self.settings.ollama_model}")
        return OllamaGateResult(status="healthy", detail=f"model_ready:{self.settings.ollama_model}", attempts=1)

    async def _restore_state_snapshot(self) -> None:
        loaded = await self.state_manager.load_from_disk()
        if loaded:
            LOGGER.info("State snapshot restored from disk with %s project entries.", len(loaded))

    async def _subscribe_health_events(self) -> None:
        await self.event_bus.subscribe("system.heartbeat", self._record_heartbeat)
        await self.event_bus.subscribe("system.stalled", self._record_stalled)
        await self.event_bus.subscribe("system.recovered", self._record_recovered)
        await self.event_bus.subscribe("error.occurred", self._record_error)

    async def _record_heartbeat(self, payload: dict[str, Any]) -> None:
        await self._write_status(lifecycle="running", detail="heartbeat", last_heartbeat=payload.get("timestamp"))

    async def _record_stalled(self, payload: dict[str, Any]) -> None:
        await self._write_status(
            lifecycle="running",
            detail="stalled",
            stalled=True,
            stalled_since=payload.get("timestamp"),
        )

    async def _record_recovered(self, payload: dict[str, Any]) -> None:
        await self._write_status(lifecycle="running", detail="recovered", recovery=payload.get("payload", {}))

    async def _record_error(self, payload: dict[str, Any]) -> None:
        await self._write_status(lifecycle="running", detail="error", last_error=payload.get("payload", {}))

    async def _write_pid_file(self) -> None:
        await aiofiles.os.makedirs(self.settings.daemon_pid_path.parent, exist_ok=True)
        async with aiofiles.open(self.settings.daemon_pid_path, "w", encoding="utf-8") as handle:
            await handle.write(str(os.getpid()))

    async def _remove_pid_file(self) -> None:
        try:
            await aiofiles.os.remove(self.settings.daemon_pid_path)
        except FileNotFoundError:
            return

    async def _write_status(self, **updates: Any) -> Path:
        payload = {
            "pid": os.getpid(),
            "app_name": self.settings.app_name,
            **self._last_health,
            **updates,
        }
        self._last_health = payload
        await aiofiles.os.makedirs(self.settings.daemon_status_path.parent, exist_ok=True)
        async with aiofiles.open(self.settings.daemon_status_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(payload, indent=2, ensure_ascii=True))
        return self.settings.daemon_status_path


async def run_daemon(*, enable_cli: bool = False, enable_telegram: bool = True) -> None:
    daemon = OrchestratorDaemon(enable_cli=enable_cli, enable_telegram=enable_telegram)
    daemon.install_signal_handlers()
    try:
        await daemon.start()
        await daemon.wait_forever()
    finally:
        await daemon.shutdown("main_exit")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Development Team Orchestrator daemon runner")
    parser.add_argument("--cli", action="store_true", help="Enable the Textual CLI interface")
    parser.add_argument("--no-telegram", action="store_true", help="Disable the Telegram interface")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run_daemon(enable_cli=args.cli, enable_telegram=not args.no_telegram))


if __name__ == "__main__":
    main()
