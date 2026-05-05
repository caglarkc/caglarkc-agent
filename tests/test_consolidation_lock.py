from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.core.consolidation_lock import (
    read_last_consolidated_ms,
    rollback_consolidation_lock,
    try_acquire_consolidation_lock,
)


@pytest.mark.asyncio
async def test_acquire_and_rollback_roundtrip(tmp_path: Path) -> None:
    lock_path = tmp_path / ".consolidate-lock"
    prior = await try_acquire_consolidation_lock(lock_path, holder_stale_ms=3600_000.0)
    assert prior == 0.0
    assert lock_path.exists()
    assert int(lock_path.read_text(encoding="utf-8").strip()) == os.getpid()

    await rollback_consolidation_lock(lock_path, prior_ms=0.0)
    assert not lock_path.exists()


@pytest.mark.asyncio
async def test_read_last_consolidated_ms_missing(tmp_path: Path) -> None:
    lock_path = tmp_path / ".consolidate-lock"
    assert await read_last_consolidated_ms(lock_path) == 0.0


@pytest.mark.asyncio
async def test_blocks_when_holder_pid_is_live(tmp_path: Path) -> None:
    lock_path = tmp_path / ".consolidate-lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    lock_path.touch()
    result = await try_acquire_consolidation_lock(lock_path, holder_stale_ms=3600_000.0)
    assert result is None


@pytest.mark.asyncio
async def test_rollback_restores_prior_mtime(tmp_path: Path) -> None:
    lock_path = tmp_path / ".consolidate-lock"
    prior_ms = 1_700_000_000_000.0
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")

    await rollback_consolidation_lock(lock_path, prior_ms=prior_ms)
    got = await read_last_consolidated_ms(lock_path)
    assert abs(got - prior_ms) < 5.0
