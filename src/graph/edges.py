from __future__ import annotations

from langgraph.graph import END


def route_after_planner(state: dict) -> str:
    if state.get("sprint_status") == "fail":
        return END
    if state.get("awaiting_approval"):
        return END
    return "dispatcher"


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
    return "validator"


def route_after_review(state: dict) -> str:
    sprint_status = state.get("sprint_status")
    if state.get("scope_changed"):
        return "planner"
    if sprint_status in {"revision", "active"}:
        return "dispatcher"
    return END
