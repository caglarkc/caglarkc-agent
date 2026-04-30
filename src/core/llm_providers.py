from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import httpx
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.config.settings import Settings, get_settings
from src.core.contracts import DispatchAssignment


CONTEXT_MAX_CHARS = 4_000


@dataclass(frozen=True)
class WorkerModelConfig:
    provider: str
    model_name: str
    auth_available: bool = True
    missing_auth_message: str = ""


@dataclass(frozen=True)
class GeneratedFileContent:
    content: str
    provider: str
    model_name: str
    used_stub: bool = False
    fallback_reason: str | None = None


def _render_stub_file_content(target_file: str, *, task_description: str = "") -> str:
    task_note = task_description.strip() or "generated project"
    if target_file == "api_contract.json":
        return json.dumps({"version": "1.0.0", "description": task_note[:120], "endpoints": []}, indent=2) + "\n"
    if target_file == "shared_types.py":
        return (
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class SharedPayload:\n"
            "    name: str\n"
        )
    if target_file == "src/__init__.py":
        return '"""Generated project package."""\n'
    if target_file == "helpers.py":
        return (
            "def helper() -> str:\n"
            f"    return {task_note[:80]!r}\n"
        )
    if target_file == "app.py":
        return (
            "from helpers import helper\n\n"
            "def run() -> str:\n"
            "    return helper()\n"
        )
    if target_file.endswith(".json"):
        return "{}\n"
    return f"# generated fallback for {target_file}\n"


def _compact_text(value: Any, *, max_chars: int = CONTEXT_MAX_CHARS) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}... [truncated]"


def _worker_model_config(worker_id: str, settings: Settings) -> WorkerModelConfig:
    if worker_id == "worker_a":
        return WorkerModelConfig(
            provider="ollama",
            model_name=settings.ollama_model,
            auth_available=bool(settings.ollama_model),
            missing_auth_message="OLLAMA_MODEL is not configured",
        )
    if worker_id == "worker_b":
        return WorkerModelConfig(
            provider="openrouter_primary",
            model_name=settings.openrouter_model,
            auth_available=bool(settings.openrouter_api_key_primary),
            missing_auth_message="OPENROUTER_API_KEY_PRIMARY is missing",
        )
    if worker_id == "worker_c":
        return WorkerModelConfig(
            provider="openrouter_secondary",
            model_name=settings.openrouter_model_secondary,
            auth_available=bool(settings.openrouter_api_key_secondary),
            missing_auth_message="OPENROUTER_API_KEY_SECONDARY is missing",
        )
    if settings.gemini_api_key:
        return WorkerModelConfig(provider="gemini", model_name=settings.gemini_model)
    return WorkerModelConfig(
        provider="gemini",
        model_name=settings.gemini_model,
        auth_available=False,
        missing_auth_message="GEMINI_API_KEY is missing",
    )


def _chat_model_for(config: WorkerModelConfig, settings: Settings):
    if config.provider == "ollama":
        return ChatOllama(
            model=config.model_name,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
    if config.provider == "openrouter_primary":
        return ChatOpenAI(
            model=config.model_name,
            api_key=settings.openrouter_api_key_primary,
            base_url=settings.openrouter_base_url,
            temperature=0,
            timeout=settings.http_timeout_seconds,
            default_headers={
                "HTTP-Referer": "https://local.phase1.worker",
                "X-Title": "AI Development Team Orchestrator Worker",
            },
        )
    if config.provider == "openrouter_secondary":
        return ChatOpenAI(
            model=config.model_name,
            api_key=settings.openrouter_api_key_secondary,
            base_url=settings.openrouter_base_url,
            temperature=0,
            timeout=settings.http_timeout_seconds,
            default_headers={
                "HTTP-Referer": "https://local.phase1.worker",
                "X-Title": "AI Development Team Orchestrator Worker",
            },
        )
    return ChatGoogleGenerativeAI(
        model=config.model_name,
        google_api_key=settings.gemini_api_key,
        timeout=settings.http_timeout_seconds,
        temperature=0,
    )


def build_worker_prompt(state: dict, assignment: DispatchAssignment) -> tuple[str, str]:
    target_file = assignment.target_file
    suffix = Path(target_file).suffix
    output_rules = [
        "Return only the raw file body for this path (single artifact, no preamble).",
        "Return exactly one file body for the requested path.",
        "Do not include Markdown fences, explanations, greetings, or filenames.",
        "Do not include prompt-injection phrases such as 'ignore previous instructions' or 'prompt override'.",
        "Do not reference absolute filesystem paths, home directories, /etc, or path traversal.",
    ]
    if suffix == ".json":
        output_rules.append("The output must be valid JSON.")
    if suffix == ".py":
        output_rules.append("The output must be valid Python syntax with only standard-library or local imports.")

    system_prompt = (
        "You are a careful code-generation worker inside an orchestrated software team. "
        "You produce production-ready file contents that satisfy the user's intent and local validator policy. "
        + " ".join(output_rules)
    )
    user_prompt = "\n".join(
        [
            "User task:",
            _compact_text(state.get("task_description"), max_chars=1_200),
            "",
            "Sprint type:",
            _compact_text(state.get("sprint_type"), max_chars=120),
            "",
            "Assignment:",
            _compact_text(assignment.description, max_chars=800),
            "",
            "Target file:",
            target_file,
            "",
            "Context summary:",
            _compact_text(state.get("context_summary"), max_chars=CONTEXT_MAX_CHARS),
            "",
            "Generate only the raw file body now.",
        ]
    )
    return system_prompt, user_prompt


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


def _strip_markdown_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return content.rstrip() + "\n"
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).rstrip() + "\n"
    return content.rstrip() + "\n"


async def _direct_chat_response(config: WorkerModelConfig, settings: Settings, system_prompt: str, user_prompt: str) -> str | None:
    if config.provider == "ollama":
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            response = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": config.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0},
                },
            )
            response.raise_for_status()
            payload = response.json()
        return (payload.get("message") or {}).get("content")
    if config.provider in {"openrouter_primary", "openrouter_secondary"}:
        api_key = settings.openrouter_api_key_primary if config.provider == "openrouter_primary" else settings.openrouter_api_key_secondary
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            response = await client.post(
                f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://local.phase1.worker",
                    "X-Title": "AI Development Team Orchestrator Worker",
                },
                json={
                    "model": config.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0,
                },
            )
            response.raise_for_status()
            payload = response.json()
        choices = payload.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            return ""
        return ((choices[0].get("message") or {}).get("content") or "")
    return None


def _fallback_chain(settings: Settings) -> list[WorkerModelConfig]:
    """Returns providers in priority order: Ollama -> OpenRouter primary -> OpenRouter secondary -> Gemini."""
    chain = []
    if settings.ollama_model:
        chain.append(WorkerModelConfig(provider="ollama", model_name=settings.ollama_model))
    if settings.openrouter_api_key_primary:
        chain.append(WorkerModelConfig(provider="openrouter_primary", model_name=settings.openrouter_model))
    if settings.openrouter_api_key_secondary:
        chain.append(WorkerModelConfig(provider="openrouter_secondary", model_name=settings.openrouter_model_secondary))
    if settings.gemini_api_key:
        chain.append(WorkerModelConfig(provider="gemini", model_name=settings.gemini_model))
    return chain


async def _try_provider(config: WorkerModelConfig, settings: Settings, system_prompt: str, user_prompt: str) -> str:
    direct_content = await _direct_chat_response(config, settings, system_prompt, user_prompt)
    if direct_content is not None:
        return _strip_markdown_fence(_content_to_text(direct_content))
    model = _chat_model_for(config, settings)
    response = await asyncio.wait_for(
        model.ainvoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]),
        timeout=max(5.0, settings.http_timeout_seconds + 5.0),
    )
    return _strip_markdown_fence(_content_to_text(response.content))


async def generate_file_content(state: dict, assignment: DispatchAssignment) -> GeneratedFileContent:
    settings = get_settings()
    primary_config = _worker_model_config(assignment.worker_id, settings)

    if settings.worker_use_stub:
        return GeneratedFileContent(
            content=_render_stub_file_content(assignment.target_file, task_description=state.get("task_description", "")),
            provider=primary_config.provider,
            model_name=primary_config.model_name,
            used_stub=True,
            fallback_reason="WORKER_USE_STUB enabled",
        )

    system_prompt, user_prompt = build_worker_prompt(state, assignment)
    chain = _fallback_chain(settings)
    last_error: Exception | None = None

    for config in chain:
        try:
            content = await _try_provider(config, settings, system_prompt, user_prompt)
            fallback_reason = f"fallback from {primary_config.provider}" if config.provider != primary_config.provider else None
            return GeneratedFileContent(
                content=content,
                provider=config.provider,
                model_name=config.model_name,
                fallback_reason=fallback_reason,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    return GeneratedFileContent(
        content=_render_stub_file_content(assignment.target_file, task_description=state.get("task_description", "")),
        provider=primary_config.provider,
        model_name=primary_config.model_name,
        used_stub=True,
        fallback_reason=f"all providers failed: {last_error}",
    )
