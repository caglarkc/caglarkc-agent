from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os

from src.config.settings import get_settings


class ProjectManager:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def ensure_project_structure(self, project_name: str) -> Path:
        project_root = self._settings.projects_root / project_name
        await aiofiles.os.makedirs(project_root / ".meta" / "sprints", exist_ok=True)
        return project_root

    async def write_plan(self, project_name: str, payload: dict[str, Any]) -> Path:
        project_root = await self.ensure_project_structure(project_name)
        plan_path = project_root / ".meta" / "plan.json"
        async with aiofiles.open(plan_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(payload, indent=2, ensure_ascii=True))
        return plan_path

    async def read_plan(self, project_name: str) -> dict[str, Any] | None:
        plan_path = self._settings.projects_root / project_name / ".meta" / "plan.json"
        if not plan_path.exists():
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
