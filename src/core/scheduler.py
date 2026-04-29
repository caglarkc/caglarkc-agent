from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from src.core.retry_policy import classify_error


@dataclass
class ScheduledTask:
    project_id: str
    thread_id: str
    task_id: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class DispatchDecision:
    task: ScheduledTask | None
    reason: str


class FairScheduler:
    def __init__(self, *, per_project_limit: int = 1) -> None:
        self.per_project_limit = per_project_limit
        self._queues: dict[str, deque[ScheduledTask]] = {}
        self._round_robin: deque[str] = deque()
        self._active_counts: dict[str, int] = {}
        self._throttled: dict[str, str] = {}
        self._archived: set[str] = set()

    def register_project(self, project_id: str) -> None:
        if project_id not in self._queues:
            self._queues[project_id] = deque()
            self._round_robin.append(project_id)
            self._active_counts[project_id] = 0

    def enqueue(self, task: ScheduledTask) -> None:
        self.register_project(task.project_id)
        self._queues[task.project_id].append(task)

    def archive_project(self, project_id: str) -> None:
        self._archived.add(project_id)

    def restore_project(self, project_id: str) -> None:
        self._archived.discard(project_id)

    def acquire_next(self) -> DispatchDecision:
        if not self._round_robin:
            return DispatchDecision(task=None, reason="no_registered_projects")
        for _ in range(len(self._round_robin)):
            project_id = self._round_robin[0]
            self._round_robin.rotate(-1)
            if project_id in self._archived:
                continue
            if self._throttled.get(project_id):
                continue
            if self._active_counts.get(project_id, 0) >= self.per_project_limit:
                continue
            queue = self._queues.get(project_id, deque())
            if not queue:
                continue
            task = queue.popleft()
            self._active_counts[project_id] = self._active_counts.get(project_id, 0) + 1
            return DispatchDecision(task=task, reason="scheduled")
        if any(self._throttled.values()):
            return DispatchDecision(task=None, reason="throttled")
        return DispatchDecision(task=None, reason="all_projects_at_capacity_or_empty")

    def release(self, project_id: str) -> None:
        self._active_counts[project_id] = max(0, self._active_counts.get(project_id, 0) - 1)

    def throttle_project(self, project_id: str, reason: str) -> None:
        self.register_project(project_id)
        self._throttled[project_id] = reason

    def clear_throttle(self, project_id: str) -> None:
        self._throttled.pop(project_id, None)

    def handle_provider_error(self, project_id: str, exc: Exception) -> str:
        classification = classify_error(exc)
        if classification.retryable:
            self.throttle_project(project_id, classification.reason)
            return "throttled"
        return "fallback_required"

    def queue_lengths(self) -> dict[str, int]:
        return {project_id: len(queue) for project_id, queue in self._queues.items()}
