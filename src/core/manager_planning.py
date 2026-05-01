from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, ConfigDict, ValidationError

from src.config.settings import Settings, get_settings
from src.core.contracts import ExecutionIntent, PlanConversationTurn, PlanDraft, PlannedFile


EXECUTION_KEYWORDS = (
    "uygula",
    "kod yaz",
    "sprint baslat",
    "baslat",
    "start sprint",
    "apply",
    "implement",
    "ship it",
    "go build",
)
EXECUTION_NEGATION_PATTERNS = (
    "kod yazma",
    "kod yazmayalim",
    "kod yazmayın",
    "uygulama",
    "baslatma",
    "başlatma",
    "henuz kod yazma",
    "henüz kod yazma",
    "henuz uygulama",
    "henüz uygulama",
    "do not implement",
    "don't implement",
    "dont implement",
    "do not apply",
    "don't apply",
    "dont apply",
    "not yet",
)


class PlanningModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply_text: str
    needs_clarification: bool = False
    execution_intent: Literal["discuss", "apply"] = "discuss"
    plan: PlanDraft | None = None


@dataclass(frozen=True)
class ManagerPlanningResult:
    reply_text: str
    draft_plan: PlanDraft | None
    execution_intent: ExecutionIntent
    needs_clarification: bool = False
    used_fallback: bool = False
    error_message: str | None = None


class ManagerPlanningService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        model: Any | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._model = model

    async def process_turn(
        self,
        *,
        user_message: str,
        conversation_history: list[dict[str, Any]] | list[PlanConversationTurn],
        existing_draft: dict[str, Any] | PlanDraft | None,
        explicit_execution: bool = False,
    ) -> ManagerPlanningResult:
        normalized_intent = detect_execution_intent(user_message, explicit=explicit_execution)
        parsed_history = self._normalize_history(conversation_history)
        draft = self._normalize_draft(existing_draft)
        if not self._settings.manager_use_gemini:
            return self._heuristic_plan(
                user_message=user_message,
                conversation_history=parsed_history,
                existing_draft=draft,
                execution_intent=normalized_intent,
            )
        if not self._settings.gemini_api_key and self._model is None:
            return ManagerPlanningResult(
                reply_text=(
                    "Planning mode hazir ama Gemini baglantisi icin `GEMINI_API_KEY` eksik. "
                    "Ana beyin baglanmadan onay akisi baslatilmadi."
                ),
                draft_plan=draft,
                execution_intent=normalized_intent,
                needs_clarification=True,
                error_message="GEMINI_API_KEY is missing",
            )

        try:
            raw_response = await asyncio.wait_for(
                self._invoke_model(
                    user_message=user_message,
                    conversation_history=parsed_history,
                    existing_draft=draft,
                    execution_intent=normalized_intent,
                ),
                timeout=max(5.0, self._settings.http_timeout_seconds + 5.0),
            )
        except Exception as exc:  # noqa: BLE001
            fallback = self._heuristic_plan(
                user_message=user_message,
                conversation_history=parsed_history,
                existing_draft=draft,
                execution_intent=normalized_intent,
            )
            fallback_plan = _normalize_plan_for_request(
                fallback.draft_plan,
                user_message=user_message,
                conversation_history=parsed_history,
            )
            return ManagerPlanningResult(
                reply_text=(
                    f"Gemini planlama yaniti alinamadi ({type(exc).__name__}). "
                    f"Kontrollu fallback ile devam ediyorum: {fallback.reply_text}"
                ),
                draft_plan=fallback_plan,
                execution_intent=fallback.execution_intent,
                needs_clarification=fallback.needs_clarification,
                used_fallback=True,
                error_message=f"gemini_invoke_failed:{type(exc).__name__}",
            )
        parsed = await self._parse_with_repair(raw_response)
        if parsed is None:
            preview = (raw_response or "")[:200].replace("\n", " ")
            return ManagerPlanningResult(
                reply_text=(
                    f"Gemini yaniti yapisal olarak gecersiz. Ham yanit: {preview!r}. "
                    "Kapsami netlestirelim; worker akisi baslatilmadi."
                ),
                draft_plan=draft,
                execution_intent=ExecutionIntent(
                    mode="discuss",
                    explicit=normalized_intent.explicit,
                    reason="planner_response_invalid",
                ),
                needs_clarification=True,
                error_message="manager_response_invalid",
            )

        final_intent = ExecutionIntent(
            mode=normalized_intent.mode,
            explicit=normalized_intent.explicit,
            reason=normalized_intent.reason or parsed.execution_intent,
        )
        fallback_plan = parsed.plan or draft or _heuristic_draft_from_message(
            _combined_user_text(user_message, parsed_history),
            existing_draft=draft,
        )
        final_plan = _normalize_plan_for_request(
            fallback_plan,
            user_message=user_message,
            conversation_history=parsed_history,
        )
        return ManagerPlanningResult(
            reply_text=parsed.reply_text.strip(),
            draft_plan=final_plan,
            execution_intent=final_intent,
            needs_clarification=parsed.needs_clarification,
        )

    async def _invoke_model(
        self,
        *,
        user_message: str,
        conversation_history: list[PlanConversationTurn],
        existing_draft: PlanDraft | None,
        execution_intent: ExecutionIntent,
    ) -> str:
        model = self._model or ChatGoogleGenerativeAI(
            model=self._settings.manager_model or self._settings.gemini_model,
            google_api_key=self._settings.gemini_api_key,
            timeout=self._settings.http_timeout_seconds,
            temperature=0.2,
        )
        response = await model.ainvoke(
            [
                SystemMessage(content=self._system_prompt()),
                HumanMessage(
                    content=self._user_prompt(
                        user_message=user_message,
                        conversation_history=conversation_history,
                        existing_draft=existing_draft,
                        execution_intent=execution_intent,
                    )
                ),
            ]
        )
        return _content_to_text(response.content)

    async def _parse_with_repair(self, raw_response: str) -> PlanningModelResponse | None:
        parsed = self._parse_response(raw_response)
        if parsed is not None:
            return parsed
        repaired = await self._repair_response(raw_response)
        return self._parse_response(repaired)

    async def _repair_response(self, raw_response: str) -> str:
        model = self._model or ChatGoogleGenerativeAI(
            model=self._settings.manager_model or self._settings.gemini_model,
            google_api_key=self._settings.gemini_api_key,
            timeout=self._settings.http_timeout_seconds,
            temperature=0,
        )
        response = await model.ainvoke(
            [
                SystemMessage(
                    content=(
                        "You repair invalid planner outputs. Return valid JSON only with keys "
                        "`reply_text`, `needs_clarification`, `execution_intent`, and `plan`."
                    )
                ),
                HumanMessage(content=raw_response),
            ]
        )
        return _content_to_text(response.content)

    def _parse_response(self, raw_response: str) -> PlanningModelResponse | None:
        candidate = _extract_json_object(raw_response)
        if candidate is None:
            return None
        try:
            return PlanningModelResponse.model_validate(json.loads(candidate))
        except (json.JSONDecodeError, ValidationError):
            return None

    def _heuristic_plan(
        self,
        *,
        user_message: str,
        conversation_history: list[PlanConversationTurn],
        existing_draft: PlanDraft | None,
        execution_intent: ExecutionIntent,
    ) -> ManagerPlanningResult:
        plan = existing_draft or _heuristic_draft_from_message(user_message, existing_draft=existing_draft)
        if plan is None:
            reply = (
                "Isteği anladim; once kapsamı biraz daha netlestirelim. "
                "Hangi yuzeyi onceliyoruz, hangi dosyalarin cikmasini bekliyorsun?"
            )
            return ManagerPlanningResult(
                reply_text=reply,
                draft_plan=None,
                execution_intent=ExecutionIntent(mode="discuss", explicit=execution_intent.explicit, reason="needs_scope"),
                needs_clarification=True,
                used_fallback=True,
            )
        if execution_intent.mode == "apply":
            reply = (
                f"Hazir planı onaya goturuyorum: {plan.summary}. "
                "Onay gelince worker kuyruğu bu dosya listesiyle baslayacak."
            )
        else:
            history_hint = " ".join(turn.content for turn in conversation_history[-2:] if turn.role == "user")
            reply = (
                f"Su anki plan taslagi: {plan.summary}. "
                f"Oncelikli dosyalar: {', '.join(item.path for item in plan.files[:4])}. "
                f"{'Devam etmeden once ayrintilari netlestirebiliriz.' if history_hint else 'Uygulamaya gecmek icin /apply diyebilirsin.'}"
            )
        return ManagerPlanningResult(
            reply_text=reply,
            draft_plan=plan,
            execution_intent=execution_intent,
            needs_clarification=execution_intent.mode != "apply",
            used_fallback=True,
        )

    def _normalize_history(
        self,
        conversation_history: list[dict[str, Any]] | list[PlanConversationTurn],
    ) -> list[PlanConversationTurn]:
        history: list[PlanConversationTurn] = []
        for item in conversation_history[-self._settings.manager_max_history_turns :]:
            if isinstance(item, PlanConversationTurn):
                history.append(item)
                continue
            try:
                history.append(PlanConversationTurn.model_validate(item))
            except ValidationError:
                continue
        return history

    def _normalize_draft(self, existing_draft: dict[str, Any] | PlanDraft | None) -> PlanDraft | None:
        if existing_draft is None:
            return None
        if isinstance(existing_draft, PlanDraft):
            return existing_draft
        try:
            return PlanDraft.model_validate(existing_draft)
        except ValidationError:
            return None

    def _system_prompt(self) -> str:
        return (
            "You are the primary planning manager for a local AI orchestration daemon. "
            "Default behavior is planning, scoping, and clarification in the user's language. "
            "Do not assume code generation should start unless the user explicitly asks to apply, implement, "
            "write code, or start a sprint. Return valid JSON only. "
            "If the scope is clear enough, include a plan with the concrete files that match the user's request. "
            "If not, ask focused follow-up questions and leave `plan` as null. "
            "Never default to the fixed trio api_contract.json/shared_types.py/src/__init__.py unless the task truly needs them."
        )

    def _user_prompt(
        self,
        *,
        user_message: str,
        conversation_history: list[PlanConversationTurn],
        existing_draft: PlanDraft | None,
        execution_intent: ExecutionIntent,
    ) -> str:
        history_payload = [turn.model_dump() for turn in conversation_history]
        return json.dumps(
            {
                "instruction": (
                    "Reply in JSON with keys reply_text, needs_clarification, execution_intent, and plan. "
                    "execution_intent must be either discuss or apply. "
                    "plan must be null or an object with summary, sprint_type, and files[]. "
                    "Each file needs path, description, dependencies, and task_type."
                ),
                "user_message": user_message,
                "detected_intent": execution_intent.model_dump(),
                "conversation_history": history_payload,
                "existing_draft": existing_draft.model_dump() if existing_draft else None,
            },
            ensure_ascii=True,
        )


def detect_execution_intent(message: str, *, explicit: bool = False) -> ExecutionIntent:
    lowered = " ".join((message or "").lower().split())
    if explicit:
        return ExecutionIntent(mode="apply", explicit=True, reason="explicit_execution_request")
    if any(pattern in lowered for pattern in EXECUTION_NEGATION_PATTERNS):
        return ExecutionIntent(mode="discuss", explicit=False, reason="execution_negated")
    if any(keyword in lowered for keyword in EXECUTION_KEYWORDS):
        return ExecutionIntent(mode="apply", explicit=True, reason="explicit_execution_request")
    return ExecutionIntent(mode="discuss", explicit=False, reason="planning_default")


def draft_to_queue(
    draft: PlanDraft,
    *,
    project_id: str,
    thread_id: str,
    sprint_id: str,
) -> tuple[list[dict[str, Any]], dict[str, list[str]], dict[str, str]]:
    from uuid import uuid4

    from src.core.contracts import DispatchAssignment

    queue: list[dict[str, Any]] = []
    dependencies: dict[str, list[str]] = {}
    file_registry: dict[str, str] = {}
    for item in draft.files:
        dependencies[item.path] = list(item.dependencies)
        file_registry[item.path] = "planned"
        queue.append(
            {
                "assignment": DispatchAssignment(
                    task_id=str(uuid4()),
                    project_id=project_id,
                    thread_id=thread_id,
                    sprint_id=sprint_id,
                    worker_id="unassigned",
                    target_file=item.path,
                    description=item.description,
                    correlation_id=project_id,
                    metadata={"kind": draft.sprint_type, "task_type": item.task_type},
                ).model_dump(),
                "status": "planned",
                "validation_error": None,
                "retry_count": 0,
                "blocked_by": [],
                "task_type": item.task_type,
            }
        )
    return queue, dependencies, file_registry


def _heuristic_draft_from_message(user_message: str, *, existing_draft: PlanDraft | None = None) -> PlanDraft | None:
    text = (user_message or "").strip()
    if not text:
        return existing_draft
    lowered = text.lower()
    if "api" in lowered:
        files = [
            PlannedFile(path="api_contract.json", description="Define the API surface for the requested service.", dependencies=[], task_type="contract_spec"),
            PlannedFile(path="app.py", description="Implement the API entrypoint.", dependencies=["api_contract.json"], task_type="feature_entry"),
            PlannedFile(path="tests/test_api.py", description="Cover the main API flow.", dependencies=["app.py"], task_type="test_file"),
        ]
        return PlanDraft(summary=text, sprint_type="feature", files=files)
    if "restoran" in lowered or "restaurant" in lowered:
        files = [
            PlannedFile(path="index.html", description="Build the restaurant landing page markup.", dependencies=[], task_type="frontend_markup"),
            PlannedFile(path="styles.css", description="Style the restaurant site with responsive layout.", dependencies=[], task_type="frontend_style"),
            PlannedFile(path="script.js", description="Add lightweight menu/reservation interactions.", dependencies=[], task_type="frontend_script"),
        ]
        return PlanDraft(summary=text, sprint_type="feature", files=files)
    if "site" in lowered or "landing" in lowered or "web" in lowered or "html" in lowered:
        debt_tracker = "borç" in lowered or "borc" in lowered or "debt" in lowered
        if debt_tracker:
            files = [
                PlannedFile(
                    path="index.html",
                    description=(
                        "Build the static debt tracking app markup with debtor form, summary totals, "
                        "filterable debt list, and empty states. It must run by opening index.html."
                    ),
                    dependencies=[],
                    task_type="frontend_markup",
                ),
                PlannedFile(
                    path="styles.css",
                    description="Style the debt tracker as a responsive, readable financial dashboard.",
                    dependencies=[],
                    task_type="frontend_style",
                ),
                PlannedFile(
                    path="script.js",
                    description=(
                        "Implement localStorage-backed debt add/edit/delete, paid/unpaid state, "
                        "search/filtering, and total calculations with no backend."
                    ),
                    dependencies=[],
                    task_type="frontend_script",
                ),
            ]
        else:
            files = [
                PlannedFile(path="index.html", description="Build the static website markup.", dependencies=[], task_type="frontend_markup"),
                PlannedFile(path="styles.css", description="Style the static website with responsive layout.", dependencies=[], task_type="frontend_style"),
                PlannedFile(path="script.js", description="Add lightweight static-site interactions.", dependencies=[], task_type="frontend_script"),
            ]
        return PlanDraft(summary=text, sprint_type="feature", files=files)
    if "modul" in lowered or "module" in lowered or "ekle" in lowered or "add" in lowered:
        files = [
            PlannedFile(path="src/module.py", description="Implement the requested module.", dependencies=[], task_type="feature_module"),
            PlannedFile(path="tests/test_module.py", description="Add focused tests for the module.", dependencies=["src/module.py"], task_type="test_file"),
        ]
        return PlanDraft(summary=text, sprint_type="feature", files=files)
    return existing_draft


def _normalize_plan_for_request(
    plan: PlanDraft | None,
    *,
    user_message: str,
    conversation_history: list[PlanConversationTurn],
) -> PlanDraft | None:
    if plan is None:
        return None
    combined = _combined_user_text(user_message, conversation_history).lower()
    wants_frontend = any(keyword in combined for keyword in ("restoran", "restaurant", "site", "web", "landing"))
    wants_three_workers = any(keyword in combined for keyword in ("3 ai", "üç ai", "uc ai", "3 ayrı", "üç ayrı", "uc ayri", "three"))
    if wants_frontend:
        frontend_suffixes = {".html", ".css", ".js"}
        normalized_files = []
        changed = False
        for item in plan.files:
            if Path(item.path).suffix.lower() in frontend_suffixes and item.dependencies:
                normalized_files.append(item.model_copy(update={"dependencies": []}))
                changed = True
            else:
                normalized_files.append(item)
        if changed:
            plan = PlanDraft(summary=plan.summary, sprint_type=plan.sprint_type or "feature", files=normalized_files)
    if not wants_frontend or not wants_three_workers or len(plan.files) >= 3:
        return plan
    return PlanDraft(
        summary=plan.summary,
        sprint_type=plan.sprint_type or "feature",
        files=[
            PlannedFile(
                path="index.html",
                description="Build the restaurant landing page markup with brand, story, menu highlights, and reservation call to action.",
                dependencies=[],
                task_type="frontend_markup",
            ),
            PlannedFile(
                path="styles.css",
                description="Create the responsive warm-professional visual design for the restaurant site.",
                dependencies=[],
                task_type="frontend_style",
            ),
            PlannedFile(
                path="script.js",
                description="Add lightweight menu and reservation interactions without external dependencies.",
                dependencies=[],
                task_type="frontend_script",
            ),
        ],
    )


def _combined_user_text(user_message: str, conversation_history: list[PlanConversationTurn]) -> str:
    return " ".join([turn.content for turn in conversation_history if turn.role == "user"] + [user_message])


def _extract_json_object(value: str) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    return match.group(0) if match else None


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)
