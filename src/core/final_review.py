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


async def _ollama_review(prompt: str) -> dict[str, Any]:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=settings.final_review_timeout_seconds) as client:
        response = await client.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are the final local code auditor. Inspect generated files and executor output. "
                            "Return only JSON with keys: approved:boolean, summary:string, issues:array. "
                            "Each issue must include target_file, code, message, severity."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0},
            },
        )
        response.raise_for_status()
        content = (response.json().get("message") or {}).get("content") or ""
    payload = _extract_json(content)
    if not payload:
        return {"approved": True, "summary": "Local final review returned non-JSON output.", "issues": [], "raw": _clip(content, limit=1_500)}
    return payload


async def _gemini_final_check(prompt: str, local_review: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return {"approved": True, "summary": "Gemini final check skipped: GEMINI_API_KEY missing.", "issues": []}
    url = f"{settings.gemini_base_url.rstrip('/')}/v1beta/models/{settings.manager_model}:generateContent"
    review_prompt = (
        "You are the Gemini project manager final checker. Return only JSON with keys: approved:boolean, summary:string, issues:array.\n\n"
        f"LOCAL_REVIEW:\n{json.dumps(local_review, ensure_ascii=False)}\n\nPROJECT_CONTEXT:\n{prompt}"
    )
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=settings.final_review_timeout_seconds) as client:
        for _ in range(3):
            try:
                response = await client.post(
                    url,
                    params={"key": settings.gemini_api_key},
                    json={"contents": [{"parts": [{"text": review_prompt}]}], "generationConfig": {"temperature": 0}},
                )
                response.raise_for_status()
                payload = response.json()
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {429, 500, 502, 503, 504}:
                    continue
                raise
        else:
            raise RuntimeError(_safe_error(last_error or RuntimeError("Gemini final check failed")))
    candidates = payload.get("candidates") or []
    parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []
    content = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
    parsed = _extract_json(content)
    if not parsed:
        return {"approved": True, "summary": "Gemini final check returned non-JSON output.", "issues": [], "raw": _clip(content, limit=1_500)}
    return parsed


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
        local_review = await _ollama_review(prompt)
    except Exception as exc:  # noqa: BLE001
        local_review = {"approved": True, "summary": f"Local final review unavailable: {_safe_error(exc)}", "issues": [], "skipped": True}
    try:
        gemini_review = await _gemini_final_check(prompt, local_review)
    except Exception as exc:  # noqa: BLE001
        gemini_review = {
            "approved": bool(local_review.get("approved", True)),
            "summary": f"Gemini final check unavailable: {_safe_error(exc)}",
            "issues": [],
            "skipped": True,
        }
    local_issues = _issues_from_review(local_review, source="local")
    gemini_issues = _issues_from_review(gemini_review, source="gemini")
    approved = bool(local_review.get("approved", True)) and bool(gemini_review.get("approved", True)) and not local_issues and not gemini_issues
    return {
        "approved": approved,
        "summary": f"local={local_review.get('summary', '')} | gemini={gemini_review.get('summary', '')}",
        "issues": [*local_issues, *gemini_issues],
        "local_review": local_review,
        "gemini_review": gemini_review,
    }
