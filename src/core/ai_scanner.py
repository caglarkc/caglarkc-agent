from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from src.config.settings import get_settings


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    available: bool
    model_name: str
    detail: str


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
                return ProviderResult(
                    provider="ollama",
                    available=True,
                    model_name=model_name,
                    detail=f"model_ready:{model_name}",
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
        return ProviderResult(
            provider="gemini",
            available=True,
            model_name=model_name,
            detail="api_key_set",
        )

    async def scan_openrouter_primary(self) -> ProviderResult:
        settings = get_settings()
        model_name = settings.openrouter_model
        if not settings.openrouter_api_key_primary:
            return ProviderResult(
                provider="openrouter_primary",
                available=False,
                model_name=model_name,
                detail="api_key_missing",
            )
        return ProviderResult(
            provider="openrouter_primary",
            available=True,
            model_name=model_name,
            detail="api_key_set",
        )

    async def scan_openrouter_secondary(self) -> ProviderResult:
        settings = get_settings()
        model_name = settings.openrouter_model_secondary
        if not settings.openrouter_api_key_secondary:
            return ProviderResult(
                provider="openrouter_secondary",
                available=False,
                model_name=model_name,
                detail="api_key_missing",
            )
        return ProviderResult(
            provider="openrouter_secondary",
            available=True,
            model_name=model_name,
            detail="api_key_set",
        )
