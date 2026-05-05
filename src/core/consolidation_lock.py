from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path

LOGGER = logging.getLogger(__name__)


async def read_last_consolidated_ms(lock_path: Path) -> float:
    """Return lock file mtime in milliseconds, or 0.0 if missing."""

    async def _stat_ms() -> float:
        def _inner() -> float:
            try:
                return lock_path.stat().st_mtime * 1000.0
            except OSError:
                return 0.0

        return await asyncio.to_thread(_inner)

    return await _stat_ms()


async def _read_lock_pid(lock_path: Path) -> int | None:
    def _read() -> int | None:
        try:
            raw = lock_path.read_text(encoding="utf-8").strip()
            pid = int(raw)
            return pid if pid > 0 else None
        except (OSError, ValueError):
            return None

    return await asyncio.to_thread(_read)


def _is_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


async def try_acquire_consolidation_lock(
    lock_path: Path,
    *,
    holder_stale_ms: float,
) -> float | None:
    """
    Acquire the consolidation lock. Returns prior last-consolidated ms for rollback,
    or None if another live holder holds a fresh lock.
    """

    async def _stat_mtime_ms() -> float | None:
        def _inner() -> float | None:
            try:
                return lock_path.stat().st_mtime * 1000.0
            except OSError:
                return None

        return await asyncio.to_thread(_inner)

    async def _write_pid() -> None:
        pid_str = str(os.getpid())

        def _inner() -> None:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(pid_str, encoding="utf-8")

        await asyncio.to_thread(_inner)

    mtime_ms = await _stat_mtime_ms()
    holder_pid = await _read_lock_pid(lock_path) if mtime_ms is not None else None
    now_ms = time.time() * 1000.0

    if mtime_ms is not None and now_ms - mtime_ms < holder_stale_ms:
        if holder_pid is not None and holder_pid != os.getpid():
            alive = await asyncio.to_thread(_is_pid_alive, holder_pid)
            if alive:
                LOGGER.debug(
                    "consolidation lock held by another live pid=%s (mtime_age_ms=%.0f)",
                    holder_pid,
                    now_ms - mtime_ms,
                )
                return None

    prior_ms = mtime_ms if mtime_ms is not None else 0.0
    await _write_pid()

    async def _verify() -> bool:
        def _inner() -> bool:
            try:
                return int(lock_path.read_text(encoding="utf-8").strip()) == os.getpid()
            except (OSError, ValueError):
                return False

        return await asyncio.to_thread(_inner)

    if not await _verify():
        return None
    return prior_ms


async def rollback_consolidation_lock(lock_path: Path, prior_ms: float) -> None:
    """Restore prior consolidation timestamp; prior_ms 0 removes the lock file."""

    async def _unlink() -> None:
        def _inner() -> None:
            try:
                lock_path.unlink()
            except OSError:
                pass

        await asyncio.to_thread(_inner)

    async def _touch_empty_prior() -> None:
        def _inner() -> None:
            try:
                lock_path.write_text("", encoding="utf-8")
                atime = mtime = prior_ms / 1000.0
                os.utime(lock_path, (atime, mtime))
            except OSError as exc:
                LOGGER.warning("consolidation lock rollback (utime) failed: %s", exc)

        await asyncio.to_thread(_inner)

    if prior_ms <= 0:
        await _unlink()
        return
    await _touch_empty_prior()
