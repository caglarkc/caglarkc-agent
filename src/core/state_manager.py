from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os
import aiofiles.ospath

from src.config.settings import get_settings


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

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            return deepcopy(self._state)

    async def reset(self) -> None:
        async with self._lock:
            self._state.clear()

    async def flush_to_disk(self, path: str | Path | None = None) -> Path:
        settings = get_settings()
        destination = Path(path or settings.state_snapshot_path)
        await aiofiles.os.makedirs(destination.parent, exist_ok=True)
        async with self._lock:
            payload = deepcopy(self._state)
        async with aiofiles.open(destination, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(payload, indent=2, ensure_ascii=True))
        return destination

    async def load_from_disk(self, path: str | Path | None = None) -> dict[str, Any]:
        settings = get_settings()
        source = Path(path or settings.state_snapshot_path)
        if not await aiofiles.ospath.exists(source):
            return {}
        async with aiofiles.open(source, "r", encoding="utf-8") as handle:
            content = await handle.read()
        payload = json.loads(content) if content.strip() else {}
        async with self._lock:
            self._state = deepcopy(payload)
            return deepcopy(self._state)
