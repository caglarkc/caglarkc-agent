from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal


NotificationLevel = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class Notification:
    level: NotificationLevel
    message: str
    event_type: str | None
    timestamp: str


class CLINotifier:
    def __init__(self, *, max_entries: int = 200) -> None:
        self._entries: deque[Notification] = deque(maxlen=max_entries)

    def info(self, message: str, *, event_type: str | None = None) -> Notification:
        return self._push("info", message, event_type=event_type)

    def warning(self, message: str, *, event_type: str | None = None) -> Notification:
        return self._push("warning", message, event_type=event_type)

    def error(self, message: str, *, event_type: str | None = None) -> Notification:
        return self._push("error", message, event_type=event_type)

    def from_event(self, event_type: str, payload: dict[str, Any] | None = None) -> Notification:
        message = payload.get("payload", {}) if isinstance(payload, dict) else {}
        suffix = ""
        if isinstance(message, dict) and message:
            key_bits = ", ".join(f"{key}={value}" for key, value in list(message.items())[:3])
            suffix = f" | {key_bits}"
        return self.info(f"{event_type}{suffix}", event_type=event_type)

    def get_entries(self) -> list[Notification]:
        return list(self._entries)

    def _push(self, level: NotificationLevel, message: str, *, event_type: str | None = None) -> Notification:
        entry = Notification(
            level=level,
            message=message,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._entries.append(entry)
        return entry
