from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any


class StateManager:
    _instance: "StateManager | None" = None

    def __new__(cls) -> "StateManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._lock = asyncio.Lock()
            cls._instance._state: dict[str, Any] = {}
        return cls._instance

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._state[key] = deepcopy(value)

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return deepcopy(self._state.get(key, default))

    async def update(self, key: str, updates: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            existing = deepcopy(self._state.get(key, {}))
            if not isinstance(existing, dict):
                existing = {}
            existing.update(updates)
            self._state[key] = existing
            return deepcopy(existing)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._state.pop(key, None)
