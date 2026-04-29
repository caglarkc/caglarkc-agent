from __future__ import annotations

from src.core.event_bus import EventBus
from src.storage.models import Decision, Project
from src.storage.repository import Repository


async def reviewer_node(state: dict) -> dict:
    repository = Repository()
    await repository.initialize()

    project = await repository.get_project(state["project_id"])
    if project is not None:
        await repository.upsert_project(
            Project(
                project_id=project.project_id,
                name=project.name,
                description=project.description,
                status="active",
                created_at=project.created_at,
                updated_at=project.updated_at,
                metadata=project.metadata,
            )
        )

    await repository.create_decision(
        Decision(
            decision_id=f"{state['project_id']}-reviewer",
            project_id=state["project_id"],
            summary="Reviewer validated the minimal graph flow.",
            rationale="All queued artifacts were marked done in the smoke workflow.",
        )
    )
    await EventBus().emit("sprint.completed", {"project_id": state["project_id"]})

    return {
        "sprint_status": "completed",
        "review_cycles": state.get("review_cycles", 0) + 1,
        "messages": [*state.get("messages", []), "reviewer completed"],
    }
