from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os
import aiofiles.ospath

from src.config.settings import get_settings
from src.core.consolidation_lock import (
    read_last_consolidated_ms,
    rollback_consolidation_lock,
    try_acquire_consolidation_lock,
)
from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.memory_paths import consolidate_lock_path, extracts_dir, memory_root_for_project, planner_memory_path
from src.core.memory_sessions import list_sprint_snapshots_touched_since
from src.storage.models import utc_now

LOGGER = logging.getLogger(__name__)

_SCHED_LOCKS: dict[str, asyncio.Lock] = {}
_TASKS: dict[str, asyncio.Task[None]] = {}

_PIPELINE_STATE_NAME = ".pipeline_state.json"


@dataclass(frozen=True)
class MemoryReviewContext:
    project_id: str
    project_name: str
    thread_id: str
    current_sprint: int
    sprint_status: str
    reviewer_decision: str
    file_registry: dict[str, Any]
    dependencies: dict[str, list[str]]
    plan_version: int


async def _read_pipeline_state(memory_root: Path) -> dict[str, Any]:
    path = memory_root / _PIPELINE_STATE_NAME
    if not await aiofiles.ospath.exists(path):
        return {}
    async with aiofiles.open(path, encoding="utf-8") as handle:
        raw = await handle.read()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


async def _write_pipeline_state(memory_root: Path, data: dict[str, Any]) -> None:
    path = memory_root / _PIPELINE_STATE_NAME
    await aiofiles.os.makedirs(memory_root, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as handle:
        await handle.write(json.dumps(data, indent=2, ensure_ascii=True))


async def _write_extract(ctx: MemoryReviewContext) -> Path:
    root = memory_root_for_project(ctx.project_name)
    dest_dir = extracts_dir(ctx.project_name)
    await aiofiles.os.makedirs(dest_dir, exist_ok=True)
    stamp = utc_now().replace(":", "-")
    path = dest_dir / f"{stamp}_s{ctx.current_sprint}_{ctx.sprint_status}.md"
    lines = [
        f"# Sprint {ctx.current_sprint} memory extract",
        "",
        f"- **Status**: {ctx.sprint_status}",
        f"- **Reviewer decision**: {ctx.reviewer_decision or 'n/a'}",
        f"- **Thread**: {ctx.thread_id}",
        f"- **Plan version**: {ctx.plan_version}",
        "",
        "## Files",
        *[f"- `{p}` → {ctx.file_registry.get(p, '?')}" for p in sorted(ctx.file_registry.keys())],
        "",
        "## Dependencies",
        *[f"- `{k}`: {', '.join(v) if v else '∅'}" for k, v in sorted(ctx.dependencies.items())],
        "",
    ]
    async with aiofiles.open(path, "w", encoding="utf-8") as handle:
        await handle.write("\n".join(lines))
    return path


async def _load_recent_extract_text(project_name: str, *, max_chars: int) -> str:
    directory = extracts_dir(project_name)
    if not await aiofiles.ospath.exists(directory):
        return ""

    async def _list_files() -> list[Path]:
        def _inner() -> list[Path]:
            paths = sorted(directory.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            return paths[:24]

        return await asyncio.to_thread(_inner)

    paths = await _list_files()
    chunks: list[str] = []
    budget = max_chars
    for path in paths:
        async with aiofiles.open(path, encoding="utf-8") as handle:
            text = await handle.read()
        header = f"\n\n### {path.name}\n\n"
        piece = header + text
        if len(piece) <= budget:
            chunks.append(piece)
            budget -= len(piece)
        else:
            chunks.append((header + text)[:budget])
            break
    return "".join(chunks).strip()


async def _consolidate_planner_memory(project_name: str, source_text: str) -> None:
    settings = get_settings()
    dest = planner_memory_path(project_name)
    await aiofiles.os.makedirs(dest.parent, exist_ok=True)

    if settings.memory_consolidation_use_llm and settings.gemini_api_key.strip():
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
            )
            sys = SystemMessage(
                content=(
                    "You consolidate durable project memory for a planner. "
                    "Output concise Markdown: key decisions, files touched, risks, open questions. "
                    "Do not invent facts not present in the input."
                )
            )
            human = HumanMessage(
                content=f"Consolidate the following extracts into planner-ready memory:\n\n{source_text[: settings.memory_consolidation_max_input_chars]}"
            )
            result = await llm.ainvoke([sys, human])
            body = str(result.content).strip() or _fallback_consolidation(source_text)
        except Exception:
            LOGGER.exception("LLM memory consolidation failed; using fallback merge")
            body = _fallback_consolidation(source_text)
    else:
        body = _fallback_consolidation(source_text)

    header = f"<!-- consolidated_at: {utc_now()} -->\n\n# Planner memory\n\n"
    async with aiofiles.open(dest, "w", encoding="utf-8") as handle:
        await handle.write(header + body)


def _fallback_consolidation(source_text: str) -> str:
    if not source_text.strip():
        return "_No extract files yet._"
    return source_text[: get_settings().memory_consolidation_max_input_chars]


async def _emit(bus: EventBus, event_type: str, project_id: str, thread_id: str, payload: dict[str, Any]) -> None:
    await bus.emit(
        event_type,
        new_event(
            event_type,
            payload=payload,
            project_id=project_id,
            thread_id=thread_id,
            correlation_id=project_id,
        ).model_dump(),
    )


async def _run_memory_pipeline(ctx: MemoryReviewContext) -> None:
    settings = get_settings()
    bus = EventBus()
    memory_root = memory_root_for_project(ctx.project_name)
    lock_path = consolidate_lock_path(ctx.project_name)

    await _emit(
        bus,
        "memory.pipeline_started",
        ctx.project_id,
        ctx.thread_id,
        {"phase": "start", "sprint": ctx.current_sprint},
    )

    try:
        await aiofiles.os.makedirs(memory_root, exist_ok=True)
        extract_path = await _write_extract(ctx)
        await _emit(
            bus,
            "memory.extract_written",
            ctx.project_id,
            ctx.thread_id,
            {"path": str(extract_path)},
        )
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("memory extract failed")
        await _emit(
            bus,
            "memory.pipeline_failed",
            ctx.project_id,
            ctx.thread_id,
            {"phase": "extract", "error": str(exc)},
        )
        await _emit(
            bus,
            "memory.pipeline_completed",
            ctx.project_id,
            ctx.thread_id,
            {"phase": "extract", "outcome": "failed"},
        )
        return

    if not settings.memory_consolidation_enabled:
        await _emit(
            bus,
            "memory.pipeline_completed",
            ctx.project_id,
            ctx.thread_id,
            {"phase": "consolidation_skipped", "reason": "disabled"},
        )
        return

    last_ms = await read_last_consolidated_ms(lock_path)
    now_ms = time.time() * 1000.0
    if last_ms > 0:
        hours_since = (now_ms - last_ms) / (1000.0 * 3600.0)
    else:
        hours_since = settings.memory_min_hours_between_runs + 1.0
    if last_ms > 0 and hours_since < settings.memory_min_hours_between_runs:
        await _emit(
            bus,
            "memory.pipeline_skipped",
            ctx.project_id,
            ctx.thread_id,
            {"reason": "min_hours", "hours_since": hours_since},
        )
        await _emit(bus, "memory.pipeline_completed", ctx.project_id, ctx.thread_id, {"phase": "gate"})
        return

    state = await _read_pipeline_state(memory_root)
    last_scan_ms = float(state.get("last_session_scan_at_ms") or 0.0)
    if now_ms - last_scan_ms < settings.memory_session_scan_interval_seconds * 1000.0:
        await _emit(
            bus,
            "memory.pipeline_skipped",
            ctx.project_id,
            ctx.thread_id,
            {"reason": "scan_throttle"},
        )
        await _emit(bus, "memory.pipeline_completed", ctx.project_id, ctx.thread_id, {"phase": "gate"})
        return

    state["last_session_scan_at_ms"] = now_ms
    await _write_pipeline_state(memory_root, state)

    sessions = await list_sprint_snapshots_touched_since(
        ctx.project_name,
        last_ms,
        exclude_sprint_numbers={ctx.current_sprint},
    )
    if len(sessions) < settings.memory_min_sessions:
        await _emit(
            bus,
            "memory.pipeline_skipped",
            ctx.project_id,
            ctx.thread_id,
            {"reason": "min_sessions", "count": len(sessions)},
        )
        await _emit(bus, "memory.pipeline_completed", ctx.project_id, ctx.thread_id, {"phase": "gate"})
        return

    prior = await try_acquire_consolidation_lock(
        lock_path,
        holder_stale_ms=settings.memory_lock_holder_stale_seconds * 1000.0,
    )
    if prior is None:
        await _emit(
            bus,
            "memory.pipeline_skipped",
            ctx.project_id,
            ctx.thread_id,
            {"reason": "lock_held"},
        )
        await _emit(bus, "memory.pipeline_completed", ctx.project_id, ctx.thread_id, {"phase": "gate"})
        return

    try:
        source = await _load_recent_extract_text(
            ctx.project_name,
            max_chars=settings.memory_consolidation_max_input_chars,
        )
        await _consolidate_planner_memory(ctx.project_name, source)
        await _emit(
            bus,
            "memory.consolidation_completed",
            ctx.project_id,
            ctx.thread_id,
            {"sessions_observed": sessions[:50]},
        )
        await _emit(bus, "memory.pipeline_completed", ctx.project_id, ctx.thread_id, {"phase": "consolidated"})
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("memory consolidation failed")
        await rollback_consolidation_lock(lock_path, prior)
        await _emit(
            bus,
            "memory.pipeline_failed",
            ctx.project_id,
            ctx.thread_id,
            {"phase": "consolidation", "error": str(exc)},
        )
        await _emit(
            bus,
            "memory.pipeline_completed",
            ctx.project_id,
            ctx.thread_id,
            {"phase": "consolidation", "outcome": "failed"},
        )


async def schedule_memory_pipeline_after_review(ctx: MemoryReviewContext) -> None:
    settings = get_settings()
    if not settings.memory_auto_enabled:
        return

    lock = _SCHED_LOCKS.setdefault(ctx.project_id, asyncio.Lock())
    async with lock:
        existing = _TASKS.get(ctx.project_id)
        if existing is not None and not existing.done():
            LOGGER.debug("memory pipeline already running for %s", ctx.project_id)
            return

        async def _wrapped() -> None:
            try:
                await _run_memory_pipeline(ctx)
            finally:
                current = asyncio.current_task()
                stored = _TASKS.get(ctx.project_id)
                if stored is current:
                    _TASKS.pop(ctx.project_id, None)

        _TASKS[ctx.project_id] = asyncio.create_task(_wrapped(), name=f"memory-pipeline:{ctx.project_id}")
