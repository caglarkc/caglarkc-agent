from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from telegram.ext import Application, ApplicationBuilder

from src.config.settings import get_settings
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.state_manager import StateManager
from src.interfaces.telegram.handlers import TelegramHandlerContext, register_handlers
from src.interfaces.telegram.notifier import TelegramNotifier


class OrchestratorTelegramBot:
    def __init__(
        self,
        *,
        token: str | None = None,
        authorized_chat_id: str | None = None,
        event_bus: EventBus | None = None,
        state_manager: StateManager | None = None,
        graph_manager: GraphManager | None = None,
        notifier: TelegramNotifier | None = None,
        application: Application | None = None,
    ) -> None:
        settings = get_settings()
        self.token = token or settings.telegram_bot_token
        self.authorized_chat_id = authorized_chat_id or settings.telegram_chat_id
        self.event_bus = event_bus or EventBus()
        self.state_manager = state_manager or StateManager()
        self.graph_manager = graph_manager
        self.application = application or ApplicationBuilder().token(self.token or "dummy-token").build()
        self.context = TelegramHandlerContext(
            event_bus=self.event_bus,
            graph_manager=self.graph_manager,
            state_manager=self.state_manager,
            authorized_chat_id=self.authorized_chat_id,
        )
        self.notifier = notifier or TelegramNotifier(send_message=self.send_message, event_bus=self.event_bus)

    def register_handlers(self) -> None:
        register_handlers(self.application, self.context)

    async def start(self) -> None:
        self.register_handlers()
        await self.notifier.subscribe()
        await self.application.initialize()
        await self.application.start()
        if getattr(self.application, "updater", None) is not None:
            await self.application.updater.start_polling()

    async def shutdown(self) -> None:
        if getattr(self.application, "updater", None) is not None:
            await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()

    async def send_message(self, text: str, kwargs: dict[str, Any]) -> None:
        if not self.authorized_chat_id:
            return
        await self.application.bot.send_message(chat_id=self.authorized_chat_id, text=text, **kwargs)
