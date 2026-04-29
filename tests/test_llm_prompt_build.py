from __future__ import annotations

from src.core.contracts import DispatchAssignment
from src.core.llm_providers import build_worker_prompt


def test_worker_prompt_contains_user_intent_and_output_contract() -> None:
    assignment = DispatchAssignment(
        task_id="task-1",
        project_id="project-1",
        thread_id="thread-1",
        worker_id="worker_b",
        target_file="app.py",
        description="Create the application entry point.",
        sprint_id="sprint-1",
        metadata={"task_type": "feature_entry"},
    )
    state = {
        "task_description": "Build a weather CLI that summarizes today's forecast.",
        "sprint_type": "feature",
        "context_summary": "helpers.py already exposes get_forecast_summary().",
    }

    system_prompt, user_prompt = build_worker_prompt(state, assignment)

    assert "raw file body" in system_prompt
    assert "valid Python syntax" in system_prompt
    assert "Build a weather CLI" in user_prompt
    assert "Create the application entry point." in user_prompt
    assert "helpers.py already exposes" in user_prompt
    assert "app.py" in user_prompt
    assert "feature" in user_prompt
