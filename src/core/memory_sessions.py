from __future__ import annotations

import asyncio
import re
from pathlib import Path

from src.core.memory_paths import sprint_snapshots_dir

_SPRINT_FILE_RE = re.compile(r"^sprint_(\d+)_v\d+\.json$")


async def list_sprint_snapshots_touched_since(
    project_name: str,
    since_ms: float,
    *,
    exclude_sprint_numbers: set[int] | None = None,
) -> list[str]:
    """
    Sprint snapshot files under `.meta/sprints/` touched after since_ms (mtime).
    Returns sorted ids like `sprint_001_v2` (stem without extension).
    """

    exclude_sprint_numbers = exclude_sprint_numbers or set()
    root = sprint_snapshots_dir(project_name)

    async def _collect() -> list[tuple[str, float, int]]:
        def _inner() -> list[tuple[str, float, int]]:
            results: list[tuple[str, float, int]] = []
            if not root.exists():
                return results
            for path in root.glob("sprint_*_v*.json"):
                match = _SPRINT_FILE_RE.match(path.name)
                if not match:
                    continue
                sprint_no = int(match.group(1))
                try:
                    mtime_ms = path.stat().st_mtime * 1000.0
                except OSError:
                    continue
                if mtime_ms <= since_ms:
                    continue
                if sprint_no in exclude_sprint_numbers:
                    continue
                results.append((path.stem, mtime_ms, sprint_no))
            return results

        return await asyncio.to_thread(_inner)

    rows = await _collect()
    rows.sort(key=lambda item: item[1])
    return [item[0] for item in rows]


async def touch_placeholder_snapshot(project_name: str, *, sprint_number: int, plan_version: int) -> Path:
    """Ensure a sprint snapshot exists so session gates see activity (tests/helpers)."""

    root = sprint_snapshots_dir(project_name)

    async def _touch() -> Path:
        def _inner() -> Path:
            root.mkdir(parents=True, exist_ok=True)
            path = root / f"sprint_{sprint_number:03d}_v{plan_version}.json"
            if not path.exists():
                path.write_text("{}", encoding="utf-8")
            else:
                path.touch()
            return path

        return await asyncio.to_thread(_inner)

    return await _touch()
