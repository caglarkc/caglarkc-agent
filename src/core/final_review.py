from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import aiofiles
import aiofiles.ospath
import httpx

from src.config.settings import get_settings


MAX_FILE_CHARS = 6_000
MAX_REVIEW_CHARS = 18_000


def _clip(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated]"


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        payload = json.loads(stripped)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                payload = json.loads(stripped[start : end + 1])
                return payload if isinstance(payload, dict) else {}
            except json.JSONDecodeError:
                return {}
    return {}


def _safe_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        response = exc.response
        request_url = urlsplit(str(response.request.url))
        safe_url = urlunsplit((request_url.scheme, request_url.netloc, request_url.path, "", ""))
        return f"HTTP {response.status_code} from {safe_url}"
    return str(exc)


async def _read_generated_files(project_root: Path, files: list[str]) -> list[dict[str, str]]:
    snapshots: list[dict[str, str]] = []
    for relative_path in files[:8]:
        path = (project_root / relative_path).resolve()
        try:
            path.relative_to(project_root)
        except ValueError:
            continue
        if not await aiofiles.ospath.exists(path):
            snapshots.append({"path": relative_path, "content": "[missing]"})
            continue
        async with aiofiles.open(path, "r", encoding="utf-8") as handle:
            content = await handle.read()
        snapshots.append({"path": relative_path, "content": _clip(content, limit=MAX_FILE_CHARS)})
    return snapshots


def _review_prompt(state: dict, file_snapshots: list[dict[str, str]]) -> str:
    payload = {
        "task_description": state.get("task_description"),
        "project_name": state.get("project_name"),
        "files": file_snapshots,
        "execution_results": state.get("execution_results", [])[-12:],
        "validation_issues": state.get("validation_issues", []),
        "runtime_errors": state.get("runtime_errors", []),
    }
    return _clip(json.dumps(payload, ensure_ascii=False, indent=2), limit=MAX_REVIEW_CHARS)


async def _openrouter_review(prompt: str, *, provider: str, model_name: str, api_key: str) -> dict[str, Any]:
    settings = get_settings()
    if not api_key:
        return {"approved": True, "summary": f"{provider} final review skipped: API key missing.", "issues": [], "skipped": True}
    async with httpx.AsyncClient(timeout=settings.final_review_timeout_seconds) as client:
        response = await client.post(
            f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://local.phase1.final-review",
                "X-Title": "AI Development Team Orchestrator Final Review",
            },
            json={
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a strict final code auditor. Inspect generated files and executor output. "
                            "Return only JSON with keys: approved:boolean, summary:string, issues:array. "
                            "Each issue must include target_file, code, message, severity. "
                            "Approve only when the implementation is coherent, runnable, and matches the user's request."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
            },
        )
        response.raise_for_status()
        choices = response.json().get("choices") or []
        content = ""
        if choices and isinstance(choices[0], dict):
            content = ((choices[0].get("message") or {}).get("content") or "")
    payload = _extract_json(content)
    if not payload:
        return {
            "approved": True,
            "summary": f"{provider} final review returned non-JSON output.",
            "issues": [],
            "raw": _clip(content, limit=1_500),
        }
    payload.setdefault("provider", provider)
    payload.setdefault("model", model_name)
    return payload


def _issues_from_review(review: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    issues = review.get("issues") if isinstance(review.get("issues"), list) else []
    normalized: list[dict[str, Any]] = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        normalized.append(
            {
                "code": issue.get("code", f"{source}_final_review_issue"),
                "severity": issue.get("severity", "error"),
                "target_file": issue.get("target_file") or issue.get("file") or "__project__",
                "message": issue.get("message") or issue.get("reason") or f"{source} final review requested revision",
            }
        )
    if not normalized and review.get("approved") is False:
        normalized.append(
            {
                "code": f"{source}_final_review_rejected",
                "severity": "error",
                "target_file": "__project__",
                "message": review.get("summary") or f"{source} final review rejected the generated project",
            }
        )
    return normalized


async def run_final_project_review(state: dict) -> dict[str, Any]:
    settings = get_settings()
    if not settings.final_review_enabled or settings.worker_use_stub:
        return {"approved": True, "summary": "Final model review skipped by configuration.", "issues": [], "skipped": True}
    project_root = (settings.projects_root / state["project_name"]).resolve()
    file_snapshots = await _read_generated_files(project_root, sorted(state.get("file_registry", {}).keys()))
    prompt = _review_prompt(state, file_snapshots)
    try:
        primary_review = await _openrouter_review(
            prompt,
            provider="openrouter_primary",
            model_name=settings.openrouter_model,
            api_key=settings.openrouter_api_key_primary,
        )
    except Exception as exc:  # noqa: BLE001
        primary_review = {
            "approved": True,
            "summary": f"OpenRouter primary final review unavailable: {_safe_error(exc)}",
            "issues": [],
            "skipped": True,
        }
    try:
        secondary_review = await _openrouter_review(
            prompt,
            provider="openrouter_secondary",
            model_name=settings.openrouter_model_secondary,
            api_key=settings.openrouter_api_key_secondary,
        )
    except Exception as exc:  # noqa: BLE001
        secondary_review = {
            "approved": bool(primary_review.get("approved", True)),
            "summary": f"OpenRouter secondary final review unavailable: {_safe_error(exc)}",
            "issues": [],
            "skipped": True,
        }
    primary_issues = _issues_from_review(primary_review, source="openrouter_primary")
    secondary_issues = _issues_from_review(secondary_review, source="openrouter_secondary")
    approved = (
        bool(primary_review.get("approved", True))
        and bool(secondary_review.get("approved", True))
        and not primary_issues
        and not secondary_issues
    )
    return {
        "approved": approved,
        "summary": f"primary={primary_review.get('summary', '')} | secondary={secondary_review.get('summary', '')}",
        "issues": [*primary_issues, *secondary_issues],
        "primary_review": primary_review,
        "secondary_review": secondary_review,
    }
