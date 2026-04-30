from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles
import aiofiles.os
import aiofiles.ospath

from src.config.settings import get_settings
from src.storage.models import Project, ProjectSummary, utc_now
from src.storage.repository import Repository


class ProjectManager:
    def __init__(self, repository: Repository | None = None) -> None:
        self._settings = get_settings()
        self._repository = repository or Repository()

    async def ensure_project_structure(self, project_name: str) -> Path:
        project_root = self._settings.projects_root / project_name
        await aiofiles.os.makedirs(project_root / ".meta" / "sprints", exist_ok=True)
        await aiofiles.os.makedirs(project_root / ".meta" / "archived", exist_ok=True)
        return project_root

    async def write_plan(self, project_name: str, payload: dict[str, Any]) -> Path:
        project_root = await self.ensure_project_structure(project_name)
        plan_path = project_root / ".meta" / "plan.json"
        async with aiofiles.open(plan_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(payload, indent=2, ensure_ascii=True))
        return plan_path

    async def read_plan(self, project_name: str) -> dict[str, Any] | None:
        plan_path = self._settings.projects_root / project_name / ".meta" / "plan.json"
        if not await aiofiles.ospath.exists(plan_path):
            return None
        async with aiofiles.open(plan_path, "r", encoding="utf-8") as handle:
            content = await handle.read()
        return json.loads(content)

    async def write_context_debug(self, project_name: str, content: str) -> Path:
        project_root = await self.ensure_project_structure(project_name)
        context_path = project_root / self._settings.context_output_relative_path
        async with aiofiles.open(context_path, "w", encoding="utf-8") as handle:
            await handle.write(content)
        return context_path

    async def write_project_file(self, project_name: str, relative_path: str, content: str) -> Path:
        project_root = await self.ensure_project_structure(project_name)
        destination = project_root / Path(relative_path)
        await aiofiles.os.makedirs(destination.parent, exist_ok=True)
        async with aiofiles.open(destination, "w", encoding="utf-8") as handle:
            await handle.write(content)
        return destination

    async def update_plan_snapshot(
        self,
        project_name: str,
        *,
        sprint_number: int,
        sprint_type: str,
        status: str,
        files: list[str],
        dependencies: dict[str, list[str]],
        plan_version: int,
        scope_changed: bool = False,
    ) -> Path:
        plan = await self.read_plan(project_name) or {"name": project_name, "sprints": []}
        plan["status"] = status
        plan["current_sprint"] = sprint_number
        plan.setdefault("sprints", []).append(
            {
                "number": sprint_number,
                "type": sprint_type,
                "status": status,
                "files": files,
                "dependencies": dependencies,
                "plan_version": plan_version,
                "scope_changed": scope_changed,
            }
        )
        await self.write_plan(project_name, plan)
        project_root = await self.ensure_project_structure(project_name)
        snapshot_path = project_root / ".meta" / "sprints" / f"sprint_{sprint_number:03d}_v{plan_version}.json"
        async with aiofiles.open(snapshot_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(plan["sprints"][-1], indent=2, ensure_ascii=True))
        return snapshot_path

    async def list_projects(self, *, active_only: bool = False) -> list[Project]:
        await self._repository.initialize()
        if active_only:
            statuses = ["planning", "active", "paused", "completed"]
            projects = await self._repository.list_projects_by_status(statuses)
            return [project for project in projects if project.status != "archived"]
        return await self._repository.list_projects()

    async def get_project(self, project_ref: str) -> Project | None:
        await self._repository.initialize()
        project = await self._repository.get_project(project_ref)
        if project is not None:
            return project
        return await self._repository.get_project_by_name(project_ref)

    async def create_project(self, name: str, *, description: str = "", selected: bool = True) -> Project:
        await self._repository.initialize()
        clean_name = " ".join(name.split())
        if not clean_name:
            raise ValueError("project name is required")
        project = Project(
            project_id=f"proj-{uuid4().hex[:12]}",
            name=clean_name,
            description=description or clean_name,
            status="active",
            metadata={"selected": selected},
        )
        await self._repository.upsert_project(project)
        await self.ensure_project_structure(project.name)
        if selected:
            await self.select_active_project(project.project_id)
            project = await self._repository.get_project(project.project_id) or project
        return project

    async def select_active_project(self, project_id: str) -> Project | None:
        await self._repository.initialize()
        target = await self._repository.get_project(project_id)
        if target is None:
            return None
        for project in await self._repository.list_projects():
            metadata = dict(project.metadata)
            metadata["selected"] = project.project_id == project_id
            status = project.status
            if project.project_id == project_id and project.status == "planning":
                status = "active"
            await self._repository.update_project(project.model_copy(update={"status": status, "updated_at": utc_now(), "metadata": metadata}))
        return await self._repository.get_project(project_id)

    async def archive_project(self, project_id: str) -> Project | None:
        await self._repository.initialize()
        project = await self._repository.get_project(project_id)
        if project is None:
            return None
        metadata = dict(project.metadata)
        metadata.update({"archived": True, "archived_at": utc_now(), "selected": False})
        archived = project.model_copy(update={"status": "archived", "updated_at": utc_now(), "metadata": metadata})
        await self._repository.update_project(archived)
        project_root = await self.ensure_project_structure(project.name)
        archived_path = project_root / ".meta" / "archived" / "project.json"
        async with aiofiles.open(archived_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(archived.model_dump(), indent=2, ensure_ascii=True))
        return archived

    async def project_summary(self, project_id: str) -> ProjectSummary | None:
        await self._repository.initialize()
        return await self._repository.project_summary(project_id)

    async def project_history(self, project_ref: str) -> list[dict[str, Any]]:
        project = await self.get_project(project_ref)
        if project is None:
            return []
        sprints = await self._repository.list_sprints(project.project_id)
        return [
            {
                "number": sprint.number,
                "type": sprint.sprint_type,
                "status": sprint.status,
                "review_cycles": sprint.review_cycles,
                "plan_version": sprint.plan_version,
                "completed_at": sprint.completed_at,
            }
            for sprint in sprints
        ]

    async def active_project(self) -> Project | None:
        for project in await self.list_projects():
            if project.metadata.get("selected"):
                return project
        active_projects = await self.list_projects(active_only=True)
        return active_projects[0] if active_projects else None


def duration_seconds(started_at: str | None, completed_at: str | None) -> int:
    if not started_at or not completed_at:
        return 0
    return int((datetime.fromisoformat(completed_at) - datetime.fromisoformat(started_at)).total_seconds())
