from __future__ import annotations

from collections import defaultdict

import aiofiles
import aiofiles.ospath

from src.config.settings import get_settings
from src.core.memory_paths import planner_memory_path
from src.core.project_manager import ProjectManager
from src.storage.repository import Repository


class ContextBuilder:
    MAX_TOKENS = 2000
    MAX_CHARS = MAX_TOKENS * 4

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
        failure_patterns = self._summarize_failures(failures)
        latest_sprint = sprints[-1] if sprints else None
        planner_memory = await self._load_planner_memory_slice(project_name)
        tier0 = []
        if planner_memory.strip():
            tier0 = [f"[Tier0] Planner Memory: {planner_memory.strip()}"]
        tier1 = [
            f"[Tier1] Proje: {project_name} | Aktif Sprint: {latest_sprint.number if latest_sprint else 0} | Durum: {project.status if project else 'unknown'}",
            f"[Tier1] Mimari/Contract Kararlari: {' | '.join(item.summary for item in decisions) or 'yok'}",
        ]
        tier2_sprints = sprints[-3:]
        tier2 = [
            "[Tier2] Son Sprintler: "
            + (
                " | ".join(
                    f"#{item.number}:{item.sprint_type}:{item.status}:review={item.review_cycles}"
                    for item in tier2_sprints
                )
                or "yok"
            ),
            f"[Tier2] Failure Learning: {failure_patterns or 'yok'}",
        ]
        tier3 = [
            f"[Tier3] Son Dosyalar: {', '.join(item.path for item in files[-10:]) or 'yok'}",
            f"[Tier3] Revizyon Gecmisi: {' | '.join(item.task_type for item in failures[:10]) or 'yok'}",
        ]
        summary = self._trim_context("\n".join([*tier0, *tier1, *tier2, *tier3]))
        await self._project_manager.write_context_debug(project_name, summary)
        return summary

    def _trim_context(self, summary: str) -> str:
        if len(summary) <= self.MAX_CHARS:
            return summary
        lines = summary.splitlines()
        tier1 = [line for line in lines if line.startswith("[Tier1]")]
        tier2 = [line for line in lines if line.startswith("[Tier2]")]
        tier3 = [line for line in lines if line.startswith("[Tier3]")]
        kept = tier1[:]
        budget = self.MAX_CHARS - len("\n".join(kept))
        for bucket in (tier2, tier3):
            for line in bucket:
                if len(line) + 1 <= budget:
                    kept.append(line)
                    budget -= len(line) + 1
                else:
                    trimmed = line[: max(0, budget - 4)] + " ..."
                    if trimmed.strip():
                        kept.append(trimmed)
                    return "\n".join(kept)
        return "\n".join(kept)

    def _summarize_failures(self, failures: list) -> str:
        patterns: dict[str, list[str]] = defaultdict(list)
        for failure in failures:
            patterns[failure.worker_id].append(
                f"{failure.task_type} x{failure.retry_count} -> {failure.recommendation or 'reassign'}"
            )
        segments = [f"{worker}: {', '.join(items[:3])}" for worker, items in patterns.items()]
        return " | ".join(segments[:3])
