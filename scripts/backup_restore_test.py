from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import aiofiles
import aiofiles.os
import aiofiles.ospath

from src.config.settings import get_settings
from src.core.approval_guard import ApprovalGuard
from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.graph_manager import GraphManager
from src.core.state_manager import StateManager
from src.graph.graph import build_thread_config
from src.graph.state import build_initial_state
from src.storage.repository import Repository


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def configure_test_environment() -> tuple[Path, Path]:
    base = Path("data") / f"backup-restore-{uuid4().hex[:8]}"
    backup = base / "backup"
    if base.exists():
        shutil.rmtree(base)
    backup.mkdir(parents=True, exist_ok=True)
    os.environ["DATA_DIR"] = str(base)
    os.environ["PROJECTS_ROOT"] = str(base / "projects")
    os.environ["SQLITE_DB_PATH"] = str(base / "orchestrator.db")
    os.environ["GRAPH_CHECKPOINT_PATH"] = str(base / "checkpoints.sqlite")
    get_settings.cache_clear()
    return base, backup


async def reset_singletons() -> tuple[EventBus, StateManager]:
    bus = EventBus()
    await bus.reset()
    state_manager = StateManager()
    await state_manager.reset()
    return bus, state_manager


async def copy_file(source: Path, destination: Path) -> None:
    if not await aiofiles.ospath.exists(source):
        return
    await aiofiles.os.makedirs(destination.parent, exist_ok=True)
    async with aiofiles.open(source, "rb") as src:
        content = await src.read()
    async with aiofiles.open(destination, "wb") as dst:
        await dst.write(content)


async def create_pending_runtime_state() -> tuple[str, str]:
    bus, state_manager = await reset_singletons()
    repository = Repository()
    manager = GraphManager(
        event_bus=bus,
        state_manager=state_manager,
        repository=repository,
        approval_guard=ApprovalGuard(),
    )
    await manager.start()
    await manager.bootstrap_runtime()
    thread_id = f"thread-{uuid4()}"
    project_id = f"project-{uuid4().hex[:8]}"
    config = build_thread_config(thread_id)
    manager.register_project_thread(project_id, thread_id, config)
    initial_state = build_initial_state(
        project_name="backup-project",
        task_description="Backup restore smoke",
        project_id=project_id,
        current_thread_id=thread_id,
    )
    await manager.graph.ainvoke(initial_state, config=config)
    snapshot = await manager.graph.aget_state(config)
    await state_manager.set(project_id, snapshot.values)
    await state_manager.flush_to_disk()
    await manager.shutdown_runtime()
    return project_id, thread_id


async def run_backup_restore() -> CheckResult:
    base, backup_dir = configure_test_environment()
    settings = get_settings()
    project_id, thread_id = await create_pending_runtime_state()

    await copy_file(settings.sqlite_db_path, backup_dir / "orchestrator.db")
    await copy_file(settings.graph_checkpoint_path, backup_dir / "checkpoints.sqlite")
    await copy_file(settings.state_snapshot_path, backup_dir / "state_snapshot.json")

    await aiofiles.os.remove(settings.sqlite_db_path)
    await aiofiles.os.remove(settings.graph_checkpoint_path)
    await aiofiles.os.remove(settings.state_snapshot_path)

    await copy_file(backup_dir / "orchestrator.db", settings.sqlite_db_path)
    await copy_file(backup_dir / "checkpoints.sqlite", settings.graph_checkpoint_path)
    await copy_file(backup_dir / "state_snapshot.json", settings.state_snapshot_path)

    bus, state_manager = await reset_singletons()
    manager = GraphManager(
        event_bus=bus,
        state_manager=state_manager,
        repository=Repository(),
        approval_guard=ApprovalGuard(),
    )
    await manager.start()
    await manager.bootstrap_runtime()
    recovery = await manager.recover_pending_threads()
    recovered_state = await state_manager.get(project_id)
    approval = recovered_state.get("approval_request", {})
    await bus.emit(
        "plan.approved",
        new_event(
            "plan.approved",
            payload={"approval_id": approval["approval_id"], "decision": "approved"},
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=f"sprint-{recovered_state['current_sprint']}",
            idempotency_key=f"restore-{approval['approval_id']}",
        ).model_dump(),
    )
    await asyncio.sleep(0.1)
    final_state = await state_manager.get(project_id)
    await manager.shutdown_runtime()
    if recovery["recovered_threads"] and final_state.get("sprint_status") == "approved":
        return CheckResult("Backup Restore", True, "Backup alindi, restore edildi ve pending thread guvenli resume oldu.")
    return CheckResult("Backup Restore", False, f"Restore sonrasi resume eksik: recovery={recovery} state={final_state}")


def main() -> None:
    result = asyncio.run(run_backup_restore())
    status = "PASS" if result.passed else "FAIL"
    print(f"[{status}] {result.name}: {result.detail}")
    print(f"BACKUP_RESTORE_STATUS: {'PASS' if result.passed else 'FAIL'}")


if __name__ == "__main__":
    main()
