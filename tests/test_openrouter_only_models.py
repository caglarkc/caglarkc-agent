from __future__ import annotations

import pytest

from src.config.settings import Settings
from src.core import final_review
from src.core.llm_providers import _align_html_asset_links, _fallback_chain, _normalize_generated_artifact, _worker_model_config


def test_worker_model_config_uses_gemini_for_all_workers() -> None:
    settings = Settings(
        _env_file=None,
        GEMINI_API_KEY="gemini-key",
        GEMINI_MODEL="gemini-flash-lite-latest",
    )

    assert _worker_model_config("worker_a", settings).provider == "gemini"
    assert _worker_model_config("worker_a", settings).model_name == "gemini-flash-lite-latest"
    assert _worker_model_config("worker_b", settings).provider == "gemini"
    assert _worker_model_config("worker_c", settings).provider == "gemini"


def test_fallback_chain_is_gemini_only_even_if_other_models_are_configured() -> None:
    settings = Settings(
        _env_file=None,
        OLLAMA_MODEL="qwen2.5-coder:7b",
        OPENROUTER_API_KEY_PRIMARY="primary-key",
        OPENROUTER_API_KEY_SECONDARY="secondary-key",
        OPENROUTER_MODEL="primary-model",
        OPENROUTER_MODEL_SECONDARY="secondary-model",
        GEMINI_API_KEY="gemini-key",
    )

    assert [config.provider for config in _fallback_chain(settings)] == ["gemini"]


def test_html_generation_trims_trailing_planner_json() -> None:
    content = "<!doctype html><html><body>OK</body></html>\n{\"plan\": {}}\n"

    assert _normalize_generated_artifact(content, "index.html") == "<!doctype html><html><body>OK</body></html>\n"


def test_javascript_generation_trims_trailing_planner_json() -> None:
    content = "document.addEventListener('DOMContentLoaded', () => {});\n{\"execution_intent\":\"apply\"}\n"

    assert _normalize_generated_artifact(content, "script.js") == "document.addEventListener('DOMContentLoaded', () => {});\n"


def test_html_asset_links_align_to_planned_frontend_files() -> None:
    content = '<link rel="stylesheet" href="style.css"><script src="app.js"></script>'
    state = {"file_registry": {"index.html": "planned", "styles.css": "planned", "script.js": "planned"}}

    assert _align_html_asset_links(content, state) == '<link rel="stylesheet" href="styles.css"><script src="script.js"></script>'


@pytest.mark.asyncio
async def test_final_review_runs_gemini(monkeypatch, tmp_path) -> None:
    project_root = tmp_path / "demo-project"
    project_root.mkdir()
    (project_root / "index.html").write_text("<h1>Hello</h1>\n", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        PROJECTS_ROOT=tmp_path,
        WORKER_USE_STUB=False,
        FINAL_REVIEW_ENABLED=True,
        GEMINI_API_KEY="gemini-key",
        GEMINI_MODEL="gemini-flash-lite-latest",
        MANAGER_MODEL="gemini-flash-lite-latest",
    )
    calls: list[tuple[str, str]] = []

    async def fake_gemini_review(prompt: str, *, model_name: str, api_key: str) -> dict:
        calls.append((model_name, api_key))
        return {"approved": True, "summary": "gemini ok", "issues": []}

    monkeypatch.setattr(final_review, "get_settings", lambda: settings)
    monkeypatch.setattr(final_review, "_gemini_review", fake_gemini_review)

    result = await final_review.run_final_project_review(
        {"project_name": "demo-project", "file_registry": {"index.html": {"status": "completed"}}}
    )

    assert result["approved"] is True
    assert calls == [("gemini-flash-lite-latest", "gemini-key")]
    assert "gemini=gemini ok" in result["summary"]
