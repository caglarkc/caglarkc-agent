from __future__ import annotations

import pytest

from src.config.settings import Settings
from src.core import final_review
from src.core.llm_providers import _fallback_chain, _worker_model_config


def test_worker_model_config_uses_openrouter_pair_when_local_is_disabled() -> None:
    settings = Settings(
        _env_file=None,
        OLLAMA_MODEL="",
        OPENROUTER_API_KEY_PRIMARY="primary-key",
        OPENROUTER_API_KEY_SECONDARY="secondary-key",
        OPENROUTER_MODEL="primary-model",
        OPENROUTER_MODEL_SECONDARY="secondary-model",
    )

    assert _worker_model_config("worker_a", settings).provider == "openrouter_primary"
    assert _worker_model_config("worker_a", settings).model_name == "primary-model"
    assert _worker_model_config("worker_b", settings).provider == "openrouter_secondary"
    assert _worker_model_config("worker_b", settings).model_name == "secondary-model"
    assert _worker_model_config("worker_c", settings).provider == "openrouter_primary"


def test_fallback_chain_skips_ollama_even_if_model_is_configured() -> None:
    settings = Settings(
        _env_file=None,
        OLLAMA_MODEL="qwen2.5-coder:7b",
        OPENROUTER_API_KEY_PRIMARY="primary-key",
        OPENROUTER_API_KEY_SECONDARY="secondary-key",
        OPENROUTER_MODEL="primary-model",
        OPENROUTER_MODEL_SECONDARY="secondary-model",
        GEMINI_API_KEY="gemini-key",
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
        PROJECTS_ROOT=tmp_path,
        WORKER_USE_STUB=False,
        FINAL_REVIEW_ENABLED=True,
        OPENROUTER_API_KEY_PRIMARY="primary-key",
        OPENROUTER_API_KEY_SECONDARY="secondary-key",
        OPENROUTER_MODEL="primary-model",
        OPENROUTER_MODEL_SECONDARY="secondary-model",
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
