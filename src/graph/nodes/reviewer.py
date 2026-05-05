from __future__ import annotations

import asyncio
from copy import deepcopy
from uuid import uuid4

from src.core.contracts import new_event
from src.core.event_bus import EventBus
from src.core.final_review import run_final_project_review
from src.core.memory_pipeline import MemoryReviewContext, schedule_memory_pipeline_after_review
from src.core.project_manager import ProjectManager
from src.core.state_transaction import StateTransaction
from src.storage.models import Decision
from src.storage.repository import Repository


MAX_BLOCKING_REVIEW_CYCLES = 6


def _targets_for_issue(issue: dict, queue: list[dict]) -> list[str]:
    explicit = issue.get("target_file", "__project__")
    available = [item["assignment"]["target_file"] for item in queue]
    if explicit in available:
        return [explicit]
    message = str(issue.get("message", "")).lower()
    targets: list[str] = []
    for target in available:
        name = target.lower()
        suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ""
        if name in message or suffix in message:
            targets.append(target)
    if targets:
        return sorted(set(targets))
    if explicit == "__project__":
        frontend = [target for target in available if target.endswith((".html", ".css", ".js"))]
        return frontend or available
    return [explicit]


async def reviewer_node(state: dict) -> dict:
    repository = Repository()
    await repository.initialize()
    project_id = state["project_id"]
    thread_id = state["current_thread_id"]
    sprint_id = f"sprint-{state.get('current_sprint', 1)}"
    queue = deepcopy(state.get("worker_queue", []))
    file_registry = deepcopy(state.get("file_registry", {}))
    validation_issues = deepcopy(state.get("validation_issues", []))
    review_cycles = state.get("review_cycles", 0) + 1
    decision_summary = ""
    decision_rationale = ""

    await EventBus().emit(
        "sprint.review_started",
        new_event(
            "sprint.review_started",
            payload={"review_cycles": review_cycles},
            project_id=project_id,
            thread_id=thread_id,
            sprint_id=sprint_id,
            correlation_id=project_id,
        ).model_dump(),
    )

    pending_items = [item for item in queue if item.get("status") == "planned"]
    if validation_issues:
        if review_cycles >= 3:
            await EventBus().emit(
                "sprint.completed",
                new_event(
                    "sprint.completed",
                    payload={"result": "fail", "issues": validation_issues},
                    project_id=project_id,
                    thread_id=thread_id,
                    sprint_id=sprint_id,
                    correlation_id=project_id,
                ).model_dump(),
            )
            updates = {
                "sprint_status": "fail",
                "review_cycles": review_cycles,
                "errors": [*validation_issues],
                "messages": ["reviewer failed after max cycles"],
                "reviewer_decision": "fail",
            }
            decision_summary = "Reviewer marked sprint as fail after max revision cycles."
            decision_rationale = "; ".join(issue["message"] for issue in validation_issues[:5])
            await repository.update_sprint_status(project_id, state.get("current_sprint", 1), status="fail", review_cycles=review_cycles)
        else:
            issue_targets = {issue["target_file"] for issue in validation_issues}
            for issue in validation_issues:
                targets = _targets_for_issue(issue, queue)
                for item in queue:
                    if item["assignment"]["target_file"] in targets:
                        item["status"] = "planned"
                        item["validation_error"] = issue["message"]
                        file_registry[item["assignment"]["target_file"]] = "planned"
            for item in queue:
                if item["assignment"]["target_file"] not in issue_targets and item.get("status") == "done":
                    continue
            await EventBus().emit(
                "sprint.revision_needed",
                new_event(
                    "sprint.revision_needed",
                    payload={"issues": validation_issues},
                    project_id=project_id,
                    thread_id=thread_id,
                    sprint_id=sprint_id,
                    correlation_id=project_id,
                ).model_dump(),
            )
            updates = {
                "worker_queue": queue,
                "file_registry": file_registry,
                "sprint_status": "revision",
                "review_cycles": review_cycles,
                "messages": ["reviewer requested revision"],
                "reviewer_decision": "revision",
            }
            decision_summary = "Reviewer requested revision for validator issues."
            decision_rationale = "; ".join(f"{issue['target_file']}:{issue['code']}" for issue in validation_issues[:5])
            await repository.update_sprint_status(
                project_id,
                state.get("current_sprint", 1),
                status="revision",
                review_cycles=review_cycles,
                revision_note="validator issues present",
            )
    elif pending_items:
        updates = {
            "sprint_status": "active",
            "review_cycles": review_cycles,
            "messages": ["reviewer found pending work"],
            "reviewer_decision": "revision",
        }
        decision_summary = "Reviewer returned pending work to dispatcher."
        decision_rationale = "There are still planned items waiting to run."
        await repository.update_sprint_status(project_id, state.get("current_sprint", 1), status="active", review_cycles=review_cycles)
    elif all(status == "done" for status in file_registry.values()):
        final_review = await run_final_project_review(state)
        final_review_issues = deepcopy(final_review.get("issues", []))
        if final_review_issues:
            for issue in final_review_issues:
                affected_targets = _targets_for_issue(issue, queue)
                for item in queue:
                    if item["assignment"]["target_file"] in affected_targets:
                        item["status"] = "planned"
                        item["validation_error"] = issue["message"]
                        file_registry[item["assignment"]["target_file"]] = "planned"
            updates = {
                "worker_queue": queue,
                "file_registry": file_registry,
                "sprint_status": "revision" if review_cycles < MAX_BLOCKING_REVIEW_CYCLES else "fail",
                "review_cycles": review_cycles,
                "messages": ["reviewer requested revision after final model review"],
                "validation_issues": [],
                "revision_tasks": [
                    {"target_file": issue["target_file"], "reason": issue["message"], "code": issue["code"]}
                    for issue in final_review_issues
                ],
                "final_review": final_review,
                "reviewer_decision": "revision" if review_cycles < MAX_BLOCKING_REVIEW_CYCLES else "fail",
            }
            decision_summary = "Reviewer blocked approval after final model review."
            decision_rationale = "; ".join(f"{issue['target_file']}:{issue['code']}" for issue in final_review_issues[:5])
            await repository.update_sprint_status(
                project_id,
                state.get("current_sprint", 1),
                status=updates["sprint_status"],
                review_cycles=review_cycles,
                revision_note="final model review issues present",
            )
        else:
            await EventBus().emit(
                "sprint.completed",
                new_event(
                    "sprint.completed",
                    payload={"result": "approved", "files": list(file_registry.keys()), "final_review": final_review},
                    project_id=project_id,
                    thread_id=thread_id,
                    sprint_id=sprint_id,
                    correlation_id=project_id,
                ).model_dump(),
            )
            updates = {
                "sprint_status": "approved",
                "review_cycles": review_cycles,
                "messages": ["reviewer approved sprint"],
                "validation_issues": [],
                "revision_tasks": [],
                "contract_completed": state.get("contract_completed", False) or state.get("sprint_type") == "contract",
                "final_review": final_review,
                "reviewer_decision": "approved",
            }
            decision_summary = "Reviewer approved sprint outputs."
            decision_rationale = "All files completed, executor/validator passed, and final model review found no blocking issues."
            await repository.update_sprint_status(project_id, state.get("current_sprint", 1), status="approved", review_cycles=review_cycles)
    else:
        updates = {
            "sprint_status": "fail",
            "review_cycles": review_cycles,
            "errors": [
                {"type": "review_deadlock", "message": "No pending items completed successfully."},
            ],
            "messages": ["reviewer detected deadlock"],
            "reviewer_decision": "fail",
        }
        decision_summary = "Reviewer detected deadlock and failed sprint."
        decision_rationale = "No pending items were available and outputs were not valid."
        await repository.update_sprint_status(project_id, state.get("current_sprint", 1), status="fail", review_cycles=review_cycles)

    await repository.create_decision(
        Decision(
            decision_id=str(uuid4()),
            project_id=project_id,
            sprint_id=sprint_id,
            summary=decision_summary or "Reviewer processed sprint state.",
            rationale=decision_rationale or "No rationale provided.",
        )
    )
    if updates["sprint_status"] in {"fail", "approved"}:
        await ProjectManager().update_plan_snapshot(
            state["project_name"],
            sprint_number=state.get("current_sprint", 1),
            sprint_type=state.get("sprint_type", "feature"),
            status=updates["sprint_status"],
            files=list(file_registry.keys()),
            dependencies=state.get("dependencies", {}),
            plan_version=state.get("plan_version", 1),
        )

    async with StateTransaction(project_id) as transaction:
        persisted = transaction.state
        persisted.update(updates)
        transaction.state = persisted

    if updates.get("sprint_status") in {"approved", "fail"}:
        reg = dict(updates.get("file_registry", file_registry))
        deps: dict[str, list[str]] = {k: list(v) for k, v in (updates.get("dependencies") or state.get("dependencies") or {}).items()}
        ctx = MemoryReviewContext(
            project_id=project_id,
            project_name=state["project_name"],
            thread_id=thread_id,
            current_sprint=int(state.get("current_sprint", 1)),
            sprint_status=str(updates.get("sprint_status", "")),
            reviewer_decision=str(updates.get("reviewer_decision", "")),
            file_registry=reg,
            dependencies=deps,
            plan_version=int(state.get("plan_version", 1)),
        )
        asyncio.create_task(schedule_memory_pipeline_after_review(ctx))

    return updates
