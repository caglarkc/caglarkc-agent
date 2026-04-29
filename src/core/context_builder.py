from __future__ import annotations

from src.config.settings import get_settings
from src.core.project_manager import ProjectManager
from src.storage.repository import Repository


class ContextBuilder:
    def __init__(self, repository: Repository | None = None, project_manager: ProjectManager | None = None) -> None:
        self._settings = get_settings()
        self._repository = repository or Repository()
        self._project_manager = project_manager or ProjectManager()

    async def build(self, project_id: str, project_name: str) -> str:
        project = await self._repository.get_project(project_id)
        sprints = await self._repository.list_sprints(project_id)
        files = await self._repository.list_file_records(project_id)
        decisions = await self._repository.list_recent_decisions(
            project_id,
            limit=self._settings.context_max_decisions,
        )
        failures = await self._repository.list_worker_failures(project_id)

        latest_sprint = sprints[-1] if sprints else None
        summary = "\n".join(
            [
                f"Aktif Proje: {project_name} | Sprint: {latest_sprint.number if latest_sprint else 0} | Durum: {project.status if project else 'unknown'}",
                f"Tamamlanan Sprintler: {', '.join(f'{item.number}:{item.status}' for item in sprints) or 'yok'}",
                f"Yazilan Dosyalar: {', '.join(item.path for item in files[-5:]) or 'yok'}",
                f"Mimari Kararlar: {' | '.join(item.summary for item in decisions) or 'yok'}",
                f"Revizyon Gecmisi: {' | '.join(item.task_type for item in failures) or 'yok'}",
            ]
        )
        await self._project_manager.write_context_debug(project_name, summary)
        return summary
