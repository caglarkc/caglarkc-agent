from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.config.settings import Settings
<<<<<<< Updated upstream
from src.core.manager_planning import ManagerPlanningService
=======
from src.core.contracts import PlanConversationTurn, PlanDraft, PlannedFile
from src.core.manager_planning import ManagerPlanningService, _normalize_plan_for_request
from src.core.llm_providers import _normalize_generated_artifact
>>>>>>> Stashed changes


class FakeModel:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls = []

    async def ainvoke(self, messages):  # noqa: ANN001
        self.calls.append(messages)
        return SimpleNamespace(content=self._responses.pop(0))


class FailingModel:
    async def ainvoke(self, messages):  # noqa: ANN001, ANN201
        raise TimeoutError("provider timeout")


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


@pytest.mark.asyncio
async def test_manager_planning_does_not_let_model_escalate_to_apply() -> None:
    service = ManagerPlanningService(
        settings=Settings(
            manager_use_gemini=True,
            gemini_api_key="test-key",
            manager_model="gemini-test",
        ),
        model=FakeModel(
            [
                (
                    '{"reply_text":"Plan hazir.","needs_clarification":false,'
                    '"execution_intent":"apply","plan":{"summary":"Build CLI","sprint_type":"feature",'
                    '"files":[{"path":"main.py","description":"Create CLI.","dependencies":[],'
                    '"task_type":"feature_entry"}]}}'
                ),
            ]
        ),
    )

    result = await service.process_turn(
        user_message="CLI hesap makinesi icin plan yap, henuz kod yazma",
        conversation_history=[],
        existing_draft=None,
        explicit_execution=False,
    )

    assert result.execution_intent.mode == "discuss"
    assert result.draft_plan is not None


@pytest.mark.asyncio
async def test_manager_planning_falls_back_when_gemini_fails() -> None:
    service = ManagerPlanningService(
        settings=Settings(
            manager_use_gemini=True,
            gemini_api_key="test-key",
            manager_model="gemini-test",
            http_timeout_seconds=0.1,
        ),
        model=FailingModel(),
    )

    result = await service.process_turn(
        user_message="restoran web sitesi yap ve uygula",
        conversation_history=[],
        existing_draft=None,
        explicit_execution=True,
    )

    assert result.used_fallback is True
    assert result.execution_intent.mode == "apply"
    assert result.draft_plan is not None
    assert result.error_message == "gemini_invoke_failed:TimeoutError"


@pytest.mark.asyncio
async def test_manager_planning_normalizes_fallback_with_conversation_history() -> None:
    service = ManagerPlanningService(
        settings=Settings(
            manager_use_gemini=True,
            gemini_api_key="test-key",
            manager_model="gemini-test",
            http_timeout_seconds=0.1,
        ),
        model=FailingModel(),
    )

    result = await service.process_turn(
        user_message="Bu sohbet gecmisini planlama moduna gecir.",
        conversation_history=[
            {"role": "user", "content": "Modern restoran web sitesi istiyorum."},
            {"role": "user", "content": "Uc ayri AI worker gorevine bol."},
        ],
        existing_draft={
            "summary": "generic module",
            "sprint_type": "feature",
            "files": [
                {"path": "src/module.py", "description": "Module", "dependencies": [], "task_type": "feature_module"},
                {"path": "tests/test_module.py", "description": "Tests", "dependencies": [], "task_type": "test_file"},
            ],
        },
        explicit_execution=True,
    )

    assert result.draft_plan is not None
    assert [item.path for item in result.draft_plan.files] == ["index.html", "styles.css", "script.js"]


@pytest.mark.asyncio
async def test_manager_planning_sends_history_and_existing_draft_to_gemini() -> None:
    model = FakeModel(
        [
            (
                '{"reply_text":"Devam ediyorum.","needs_clarification":false,'
                '"execution_intent":"discuss","plan":null}'
            ),
        ]
    )
    service = ManagerPlanningService(
        settings=Settings(
            manager_use_gemini=True,
            gemini_api_key="test-key",
            manager_model="gemini-test",
        ),
        model=model,
    )

    await service.process_turn(
        user_message="renkleri koyulastir",
        conversation_history=[
            {"role": "user", "content": "landing page yap"},
            {"role": "manager", "content": "Taslak hazir."},
        ],
        existing_draft={
            "summary": "landing page yap",
            "sprint_type": "feature",
            "files": [
                {
                    "path": "app.py",
                    "description": "Create app entrypoint.",
                    "dependencies": [],
                    "task_type": "feature_entry",
                }
            ],
        },
    )

    prompt_payload = model.calls[0][1].content
    assert "landing page yap" in prompt_payload
    assert "Taslak hazir." in prompt_payload
    assert "app.py" in prompt_payload
    assert "renkleri koyulastir" in prompt_payload


@pytest.mark.asyncio
async def test_manager_planning_normalizes_frontend_three_worker_plan() -> None:
    service = ManagerPlanningService(
        settings=Settings(
            manager_use_gemini=True,
            gemini_api_key="test-key",
            manager_model="gemini-test",
        ),
        model=FakeModel(
            [
                (
                    '{"reply_text":"Plan hazir.","needs_clarification":false,'
                    '"execution_intent":"apply","plan":{"summary":"Restaurant site","sprint_type":"feature",'
                    '"files":[{"path":"index.html","description":"Markup","dependencies":[],"task_type":"frontend_markup"},'
                    '{"path":"style.css","description":"Styles","dependencies":[],"task_type":"frontend_style"}]}}'
                ),
            ]
        ),
    )

    result = await service.process_turn(
        user_message="Restoran sitesi icin plan yap. Uc ayri AI worker gorevine bol.",
        conversation_history=[
            {"role": "user", "content": "Modern restoran web sitesi istiyorum."},
        ],
        existing_draft=None,
        explicit_execution=True,
    )

    assert result.draft_plan is not None
    assert [item.path for item in result.draft_plan.files] == ["index.html", "styles.css", "script.js"]
    assert all(item.dependencies == [] for item in result.draft_plan.files)
<<<<<<< Updated upstream
=======


def test_frontend_plan_normalization_removes_runtime_reference_cycles() -> None:
    plan = PlanDraft(
        summary="restaurant site",
        sprint_type="feature",
        files=[
            PlannedFile(path="index.html", description="markup", dependencies=["style.css", "script.js"], task_type="markup"),
            PlannedFile(path="style.css", description="style", dependencies=["index.html"], task_type="style"),
            PlannedFile(path="script.js", description="script", dependencies=["index.html"], task_type="script"),
        ],
    )

    normalized = _normalize_plan_for_request(
        plan,
        user_message="uc ai ile restoran web sitesi yap",
        conversation_history=[PlanConversationTurn(role="user", content="index html style css script js olsun")],
    )

    assert normalized is not None
    assert {item.path: item.dependencies for item in normalized.files} == {
        "index.html": [],
        "style.css": [],
        "script.js": [],
    }


def test_worker_artifact_normalization_unwraps_files_payload() -> None:
    content = (
        '{"execution_intent":"apply","files":[{"path":"script.js",'
        '"content":"document.addEventListener(\\\"DOMContentLoaded\\\", () => {});"}]}'
    )

    assert _normalize_generated_artifact(content, "script.js") == 'document.addEventListener("DOMContentLoaded", () => {});\n'
>>>>>>> Stashed changes
