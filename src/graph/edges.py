from __future__ import annotations

from langgraph.graph import END


def route_after_planner(state: dict) -> str:
    if state.get("sprint_status") == "fail":
        return END
    if state.get("awaiting_approval"):
        return END
    if state.get("worker_queue"):
        return "dispatcher"
    return END


def route_after_dispatch(state: dict) -> str:
    if state.get("scope_changed"):
        return "planner"
    if state.get("sprint_status") == "fail":
        return "reviewer"
    if state.get("active_assignment") is not None:
        return "worker"
    return "reviewer"


def route_after_worker(state: dict) -> str:
    if state.get("scope_changed"):
        return "planner"
    return "executor"


def route_after_validator(state: dict) -> str:
    if state.get("scope_changed"):
        return "planner"
    if state.get("validation_issues"):
        return "reviewer"
    if any(item.get("status") == "planned" for item in state.get("worker_queue", [])):
        return "dispatcher"
    return "reviewer"


def route_after_review(state: dict) -> str:
    sprint_status = state.get("sprint_status")
    if state.get("scope_changed"):
        return "planner"
    if sprint_status in {"revision", "active"}:
        return "dispatcher"
    return END
