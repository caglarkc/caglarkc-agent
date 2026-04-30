from __future__ import annotations

import pytest

from src.config.settings import Settings
from src.core import final_review
from src.core.llm_providers import _fallback_chain, _worker_model_config


def test_worker_model_config_uses_openrouter_pair_when_local_is_disabled() -> None:
    settings = Settings(
        _env_file=None,
        ollama_model="",
        openrouter_api_key_primary="primary-key",
        openrouter_api_key_secondary="secondary-key",
        openrouter_model="primary-model",
        openrouter_model_secondary="secondary-model",
    )

    assert _worker_model_config("worker_a", settings).provider == "openrouter_primary"
    assert _worker_model_config("worker_a", settings).model_name == "primary-model"
    assert _worker_model_config("worker_b", settings).provider == "openrouter_secondary"
    assert _worker_model_config("worker_b", settings).model_name == "secondary-model"
    assert _worker_model_config("worker_c", settings).provider == "openrouter_primary"


def test_fallback_chain_skips_ollama_even_if_model_is_configured() -> None:
    settings = Settings(
        _env_file=None,
        ollama_model="qwen2.5-coder:7b",
        openrouter_api_key_primary="primary-key",
        openrouter_api_key_secondary="secondary-key",
        openrouter_model="primary-model",
        openrouter_model_secondary="secondary-model",
        gemini_api_key="gemini-key",
    )

    assert [config.provider for config in _fallback_chain(settings)] == [
        "openrouter_primary",
        "openrouter_secondary",
        "gemini",
    ]


@pytest.mark.asyncio
async def test_final_review_runs_primary_then_secondary_openrouter(monkeypatch, tmp_path) -> None:
    project_root = tmp_path / "demo-project"
    project_root.mkdir()
    (project_root / "index.html").write_text("<h1>Hello</h1>\n", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        projects_root=tmp_path,
        worker_use_stub=False,
        final_review_enabled=True,
        openrouter_api_key_primary="primary-key",
        openrouter_api_key_secondary="secondary-key",
        openrouter_model="primary-model",
        openrouter_model_secondary="secondary-model",
    )
    calls: list[tuple[str, str, str]] = []

    async def fake_openrouter_review(prompt: str, *, provider: str, model_name: str, api_key: str) -> dict:
        calls.append((provider, model_name, api_key))
        return {"approved": True, "summary": f"{provider} ok", "issues": []}

    monkeypatch.setattr(final_review, "get_settings", lambda: settings)
    monkeypatch.setattr(final_review, "_openrouter_review", fake_openrouter_review)

    result = await final_review.run_final_project_review(
        {"project_name": "demo-project", "file_registry": {"index.html": {"status": "completed"}}}
    )

    assert result["approved"] is True
    assert calls == [
        ("openrouter_primary", "primary-model", "primary-key"),
        ("openrouter_secondary", "secondary-model", "secondary-key"),
    ]
    assert "primary=openrouter_primary ok" in result["summary"]
