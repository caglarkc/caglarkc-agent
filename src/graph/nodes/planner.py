from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from src.core.context_builder import ContextBuilder
from src.core.event_bus import EventBus
from src.core.project_manager import ProjectManager
from src.storage.models import Decision, FileRecord, Project, Sprint
from src.storage.repository import Repository


async def planner_node(state: dict) -> dict:
    repository = Repository()
    project_manager = ProjectManager()
    await repository.initialize()

    project = Project(
        project_id=state["project_id"],
        name=state["project_name"],
        description=state["task_description"],
        status="planning",
    )
    await repository.upsert_project(project)

    sprint = Sprint(
        sprint_id=str(uuid4()),
        project_id=state["project_id"],
        number=state.get("current_sprint", 1),
        sprint_type="feature",
        status="planning",
    )
    await repository.create_sprint(sprint)

    queue = state.get("worker_queue") or [
        {
            "file": "README.phase1.md",
            "description": "Create a smoke-test artifact for phase 1.",
            "assigned_to": "worker_stub",
            "status": "planned",
        }
    ]
    file_registry = deepcopy(state.get("file_registry") or {})
    for job in queue:
        file_registry.setdefault(job["file"], "planned")
        await repository.create_file_record(
            FileRecord(
                file_id=str(uuid4()),
                project_id=state["project_id"],
                sprint_id=sprint.sprint_id,
                path=job["file"],
                status="planned",
                worker_id=job.get("assigned_to"),
            )
        )

    await repository.create_decision(
        Decision(
            decision_id=str(uuid4()),
            project_id=state["project_id"],
            sprint_id=sprint.sprint_id,
            summary="Phase 1 planner generated a minimal sequential workflow.",
            rationale="Smoke-test mode keeps graph execution deterministic.",
        )
    )

    context_summary = await ContextBuilder(repository=repository, project_manager=project_manager).build(
        state["project_id"],
        state["project_name"],
    )
    await project_manager.write_plan(
        state["project_name"],
        {
            "project_id": state["project_id"],
            "name": state["project_name"],
            "description": state["task_description"],
            "status": "active",
            "created_at": project.created_at,
            "sprints": [sprint.model_dump()],
            "current_sprint": sprint.number,
        },
    )
    await EventBus().emit("plan.generated", {"project_id": state["project_id"]})

    return {
        "file_registry": file_registry,
        "dependencies": state.get("dependencies", {}),
        "worker_queue": queue,
        "worker_status": {"worker_stub": "ready"},
        "sprint_type": sprint.sprint_type,
        "sprint_status": "active",
        "current_sprint": sprint.number,
        "context_summary": context_summary,
        "messages": [*state.get("messages", []), "planner completed"],
    }
