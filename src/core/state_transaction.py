from __future__ import annotations

import asyncio
from collections import defaultdict
from copy import deepcopy
from typing import Any

from src.core.state_manager import StateManager


class StateTransaction:
    """Atomic per-project mutation helper.

    Usage:
        async with StateTransaction("project-1") as tx:
            state = tx.state
            state["status"] = "approved"
            tx.state = state
    """

    _locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def __init__(self, project_id: str, state_manager: StateManager | None = None) -> None:
        self.project_id = project_id
        self.state_manager = state_manager or StateManager()
        self._lock = self._locks[project_id]
        self._snapshot: Any = None
        self.state: Any = None

    async def __aenter__(self) -> "StateTransaction":
        await self._lock.acquire()
        self._snapshot = deepcopy(self.state_manager._state.get(self.project_id))
        self.state = deepcopy(self._snapshot) if self._snapshot is not None else {}
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc is None:
                self.state_manager._state[self.project_id] = deepcopy(self.state)
            else:
                if self._snapshot is None:
                    self.state_manager._state.pop(self.project_id, None)
                else:
                    self.state_manager._state[self.project_id] = deepcopy(self._snapshot)
        finally:
            self._lock.release()
        return False
