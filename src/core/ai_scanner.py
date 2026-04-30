from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import httpx

from src.config.settings import get_settings


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    available: bool
    model_name: str
    detail: str
    latency_ms: int | None = None
    output_tokens: int | None = None
    tokens_per_second: float | None = None
    response_preview: str = ""


PING_PROMPT = "Reply with exactly: pong"


def _preview(value: Any, *, limit: int = 80) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _estimate_tokens(text: str) -> int:
    clean = " ".join((text or "").split())
    if not clean:
        return 0
    return max(1, len(clean) // 4)


def _rate(tokens: int | None, latency_ms: int | None) -> float | None:
    if not tokens or not latency_ms or latency_ms <= 0:
        return None
    return round(tokens / (latency_ms / 1000), 2)


def _elapsed_ms(started_at: float) -> int:
    return max(1, int((perf_counter() - started_at) * 1000))


class AIScanner:
    async def scan_all(self) -> list[ProviderResult]:
        return list(
            await asyncio.gather(
                self.scan_ollama(),
                self.scan_gemini(),
                self.scan_openrouter_primary(),
                self.scan_openrouter_secondary(),
            )
        )

    async def scan_ollama(self) -> ProviderResult:
        settings = get_settings()
        model_name = settings.ollama_model
        base_url = settings.ollama_base_url.rstrip("/")
        if not model_name:
            return ProviderResult(
                provider="ollama",
                available=False,
                model_name="",
                detail="disabled:OLLAMA_MODEL empty",
            )
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{base_url}/api/tags")
                response.raise_for_status()
                payload = response.json()
            models = payload.get("models", [])
            available_models = {
                str(item.get("model") or item.get("name") or "").strip()
                for item in models
                if isinstance(item, dict)
            }
            if model_name in available_models:
                started_at = perf_counter()
                async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                    chat_response = await client.post(
                        f"{base_url}/api/chat",
                        json={
                            "model": model_name,
                            "messages": [{"role": "user", "content": PING_PROMPT}],
                            "stream": False,
                            "options": {"temperature": 0, "num_predict": 32},
                        },
                    )
                    chat_response.raise_for_status()
                    chat_payload = chat_response.json()
                latency_ms = _elapsed_ms(started_at)
                content = _preview((chat_payload.get("message") or {}).get("content"))
                output_tokens = chat_payload.get("eval_count")
                if not isinstance(output_tokens, int):
                    output_tokens = _estimate_tokens(content)
                eval_duration = chat_payload.get("eval_duration")
                tokens_per_second = None
                if isinstance(eval_duration, int | float) and eval_duration > 0 and output_tokens:
                    tokens_per_second = round(output_tokens / (eval_duration / 1_000_000_000), 2)
                tokens_per_second = tokens_per_second or _rate(output_tokens, latency_ms)
                return ProviderResult(
                    provider="ollama",
                    available=True,
                    model_name=model_name,
                    detail=f"response_ok:{content or 'empty'}",
                    latency_ms=latency_ms,
                    output_tokens=output_tokens,
                    tokens_per_second=tokens_per_second,
                    response_preview=content,
                )
            return ProviderResult(
                provider="ollama",
                available=False,
                model_name=model_name,
                detail=f"model_missing:{model_name}",
            )
        except Exception as exc:
            return ProviderResult(
                provider="ollama",
                available=False,
                model_name=model_name,
                detail=f"connection_error:{exc}",
            )

    async def scan_gemini(self) -> ProviderResult:
        settings = get_settings()
        model_name = settings.manager_model or settings.gemini_model
        if not settings.gemini_api_key:
            return ProviderResult(
                provider="gemini",
                available=False,
                model_name=model_name,
                detail="api_key_missing",
            )
        started_at = perf_counter()
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.gemini_base_url.rstrip('/')}/v1beta/models/{model_name}:generateContent",
                    params={"key": settings.gemini_api_key},
                    json={
                        "contents": [{"parts": [{"text": PING_PROMPT}]}],
                        "generationConfig": {"temperature": 0, "maxOutputTokens": 32},
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            return ProviderResult(
                provider="gemini",
                available=False,
                model_name=model_name,
                detail=f"response_error:{type(exc).__name__}:{exc}",
                latency_ms=_elapsed_ms(started_at),
            )
        latency_ms = _elapsed_ms(started_at)
        parts = (
            (((payload.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
            if isinstance(payload, dict)
            else []
        )
        content = _preview("".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)))
        usage = payload.get("usageMetadata") or {}
        output_tokens = usage.get("candidatesTokenCount")
        if not isinstance(output_tokens, int):
            output_tokens = _estimate_tokens(content)
        return ProviderResult(
            provider="gemini",
            available=True,
            model_name=model_name,
            detail=f"response_ok:{content or 'empty'}",
            latency_ms=latency_ms,
            output_tokens=output_tokens,
            tokens_per_second=_rate(output_tokens, latency_ms),
            response_preview=content,
        )

    async def scan_openrouter_primary(self) -> ProviderResult:
        settings = get_settings()
        return await self._scan_openrouter(
            provider="openrouter_primary",
            model_name=settings.openrouter_model,
            api_key=settings.openrouter_api_key_primary,
        )

    async def scan_openrouter_secondary(self) -> ProviderResult:
        settings = get_settings()
        return await self._scan_openrouter(
            provider="openrouter_secondary",
            model_name=settings.openrouter_model_secondary,
            api_key=settings.openrouter_api_key_secondary,
        )

    async def _scan_openrouter(self, *, provider: str, model_name: str, api_key: str) -> ProviderResult:
        settings = get_settings()
        if not api_key:
            return ProviderResult(
                provider=provider,
                available=False,
                model_name=model_name,
                detail="api_key_missing",
            )
        started_at = perf_counter()
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://local.ai-orchestrator.scan",
                        "X-Title": "AI Development Team Orchestrator Scanner",
                    },
                    json={
                        "model": model_name,
                        "messages": [{"role": "user", "content": PING_PROMPT}],
                        "temperature": 0,
                        "max_tokens": 32,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            return ProviderResult(
                provider=provider,
                available=False,
                model_name=model_name,
                detail=f"response_error:{type(exc).__name__}:{exc}",
                latency_ms=_elapsed_ms(started_at),
            )
        latency_ms = _elapsed_ms(started_at)
        choices = payload.get("choices") or []
        message = (choices[0].get("message") or {}) if choices and isinstance(choices[0], dict) else {}
        content = _preview(message.get("content"))
        usage = payload.get("usage") or {}
        output_tokens = usage.get("completion_tokens")
        if not isinstance(output_tokens, int):
            output_tokens = _estimate_tokens(content)
        return ProviderResult(
            provider=provider,
            available=True,
            model_name=model_name,
            detail=f"response_ok:{content or 'empty'}",
            latency_ms=latency_ms,
            output_tokens=output_tokens,
            tokens_per_second=_rate(output_tokens, latency_ms),
            response_preview=content,
        )
