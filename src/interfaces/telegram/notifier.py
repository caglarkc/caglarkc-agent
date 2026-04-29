from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from src.core.event_bus import EventBus
from src.interfaces.telegram.keyboards import build_approval_keyboard


SendMessage = Callable[[str, dict[str, Any]], Awaitable[None]]


class TelegramNotifier:
    def __init__(self, *, send_message: SendMessage, event_bus: EventBus | None = None) -> None:
        self.send_message = send_message
        self.event_bus = event_bus or EventBus()

    async def subscribe(self) -> None:
        for event_name in [
            "plan.approval_needed",
            "sprint.completed",
            "sprint.revision_needed",
            "system.stalled",
            "error.occurred",
            "sprint.started",
            "sprint.worker_done",
            "sprint.review_started",
            "system.heartbeat",
        ]:
            await self.event_bus.subscribe(event_name, self.handle_event)

    async def handle_event(self, payload: dict[str, Any] | None) -> None:
        if not isinstance(payload, dict):
            return
        event_type = payload.get("event_type", "unknown")
        text, kwargs = self.message_for_event(event_type, payload)
        if text:
            await self.send_message(text, kwargs)

    def message_for_event(self, event_type: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        body = payload.get("payload", {})
        if event_type == "plan.approval_needed":
            approval_id = body.get("approval_id", "unknown")
            approval_type = body.get("approval_type", "plan")
            return (
                f"Onay gerekiyor\nApproval: {approval_id}\nTip: {approval_type}",
                {"reply_markup": build_approval_keyboard(approval_id)},
            )
        if event_type == "sprint.completed":
            return (f"Sprint tamamlandi: {body.get('result', 'approved')}", {})
        if event_type == "sprint.revision_needed":
            return ("Revizyon gerekli. Hatalı dosyaları kontrol et.", {})
        if event_type == "system.stalled":
            return ("Sistem duraksadi. Son heartbeat beklenen pencerede gelmedi.", {})
        if event_type == "error.occurred":
            return (f"Hata: {body.get('message', 'unknown error')}", {})
        if event_type == "sprint.started":
            return ("Sprint basladi.", {})
        if event_type == "sprint.worker_done":
            return (f"Worker tamamlandi: {body.get('target_file', 'unknown')}", {})
        if event_type == "sprint.review_started":
            return ("Review basladi.", {})
        return ("", {})
