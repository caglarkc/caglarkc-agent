from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.ospath
import aiosqlite
import httpx

from src.config.settings import get_settings


async def _read_json(path: Path) -> dict[str, Any]:
    if not await aiofiles.ospath.exists(path):
        return {}
    async with aiofiles.open(path, "r", encoding="utf-8") as handle:
        content = await handle.read()
    if not content.strip():
        return {}
    return json.loads(content)


async def _process_alive(pid_path: Path) -> tuple[bool, int | None]:
    if not await aiofiles.ospath.exists(pid_path):
        return False, None
    async with aiofiles.open(pid_path, "r", encoding="utf-8") as handle:
        content = await handle.read()
    pid = int(content.strip()) if content.strip() else None
    if pid is None:
        return False, None
    try:
        os.kill(pid, 0)
        return True, pid
    except OSError:
        return False, pid


async def _checkpoint_accessible(path: Path) -> bool:
    if not await aiofiles.ospath.exists(path):
        return False
    async with aiosqlite.connect(path) as connection:
        cursor = await connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
        row = await cursor.fetchone()
    return row is not None


async def _ollama_summary(base_url: str, model: str, timeout_seconds: float) -> str:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds)) as client:
            response = await client.get(f"{base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
        names = sorted({item.get("model", "") for item in payload.get("models", []) if isinstance(item, dict)})
        return "healthy" if model in names else "model_missing"
    except Exception as exc:  # noqa: BLE001
        return f"unreachable:{type(exc).__name__}"


async def gather_health() -> dict[str, Any]:
    settings = get_settings()
    status = await _read_json(settings.daemon_status_path)
    process_alive, pid = await _process_alive(settings.daemon_pid_path)
    checkpoint_ok = await _checkpoint_accessible(settings.graph_checkpoint_path)
    ollama = await _ollama_summary(
        settings.ollama_base_url,
        settings.ollama_model,
        settings.http_timeout_seconds,
    )
    telegram = "configured" if settings.telegram_bot_token and settings.telegram_chat_id else "disabled"
    return {
        "PROCESS_ALIVE": process_alive,
        "PID": pid,
        "LAST_HEARTBEAT": status.get("last_heartbeat"),
        "STALLED": bool(status.get("stalled", False)),
        "CHECKPOINT_ACCESS": checkpoint_ok,
        "TELEGRAM": telegram,
        "OLLAMA": ollama,
    }


def print_health(payload: dict[str, Any]) -> None:
    for key in ("PROCESS_ALIVE", "PID", "LAST_HEARTBEAT", "STALLED", "CHECKPOINT_ACCESS", "TELEGRAM", "OLLAMA"):
        print(f"{key}: {payload.get(key)}")


def main() -> None:
    payload = asyncio.run(gather_health())
    print_health(payload)


if __name__ == "__main__":
    main()
