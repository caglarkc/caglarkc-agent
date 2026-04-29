from __future__ import annotations

import asyncio
from collections import deque
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any


EventCallback = Callable[[Any], Awaitable[None]]


class EventBus:
    _instance: "EventBus | None" = None

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = defaultdict(list)
            cls._instance._lock = asyncio.Lock()
            cls._instance._history = deque(maxlen=500)
        return cls._instance

    async def subscribe(self, event_name: str, callback: EventCallback) -> None:
        async with self._lock:
            self._subscribers[event_name].append(callback)

    async def unsubscribe(self, event_name: str, callback: EventCallback) -> None:
        async with self._lock:
            if callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

    async def emit(self, event_name: str, payload: Any = None) -> list[Exception]:
        async with self._lock:
            callbacks = list(self._subscribers[event_name])
            self._history.append({"event_name": event_name, "payload": payload})
        tasks = [asyncio.create_task(callback(payload)) for callback in callbacks]
        if not tasks:
            await asyncio.sleep(0)
            return []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [result for result in results if isinstance(result, Exception)]

    async def reset(self) -> None:
        async with self._lock:
            self._subscribers.clear()
            self._history.clear()

    async def get_recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        async with self._lock:
            return list(self._history)[-limit:]

    async def publish(self, event_name: str, payload: Any = None) -> list[Exception]:
        return await self.emit(event_name, payload)
