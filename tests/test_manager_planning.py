from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.config.settings import Settings
from src.core.manager_planning import ManagerPlanningService


class FakeModel:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)

    async def ainvoke(self, messages):  # noqa: ANN001
        return SimpleNamespace(content=self._responses.pop(0))


@pytest.mark.asyncio
async def test_manager_planning_repairs_invalid_json() -> None:
    service = ManagerPlanningService(
        settings=Settings(
            manager_use_gemini=True,
            gemini_api_key="test-key",
            manager_model="gemini-test",
        ),
        model=FakeModel(
            [
                "not-json",
                (
                    '{"reply_text":"Plan net. Onaya hazir.","needs_clarification":false,'
                    '"execution_intent":"apply","plan":{"summary":"Build API","sprint_type":"feature",'
                    '"files":[{"path":"app.py","description":"Create the API entrypoint.","dependencies":[],'
                    '"task_type":"feature_entry"}]}}'
                ),
            ]
        ),
    )

    result = await service.process_turn(
        user_message="API tasarla ve uygula",
        conversation_history=[],
        existing_draft=None,
        explicit_execution=True,
    )

    assert result.reply_text == "Plan net. Onaya hazir."
    assert result.execution_intent.mode == "apply"
    assert result.draft_plan is not None
    assert [item.path for item in result.draft_plan.files] == ["app.py"]


@pytest.mark.asyncio
async def test_manager_planning_returns_clarification_when_json_stays_invalid() -> None:
    service = ManagerPlanningService(
        settings=Settings(
            manager_use_gemini=True,
            gemini_api_key="test-key",
            manager_model="gemini-test",
        ),
        model=FakeModel(["still-bad", "still-bad-again"]),
    )

    result = await service.process_turn(
        user_message="site kur",
        conversation_history=[],
        existing_draft=None,
        explicit_execution=False,
    )

    assert result.execution_intent.mode == "discuss"
    assert result.needs_clarification is True
    assert result.draft_plan is None
    assert result.error_message == "manager_response_invalid"
