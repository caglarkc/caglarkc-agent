from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.config.logging_config import configure_logging
from src.config.settings import get_settings
from src.graph.graph import run_minimal_graph
from src.storage.repository import Repository


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


async def check_gemini() -> CheckResult:
    settings = get_settings()
    if not settings.gemini_api_key:
        return CheckResult("Gemini", False, "GEMINI_API_KEY eksik.")

    url = (
        f"{settings.gemini_base_url}/v1beta/models/{settings.gemini_model}:generateContent"
        f"?key={settings.gemini_api_key}"
    )
    payload = {"contents": [{"parts": [{"text": "Ping"}]}]}
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.post(url, json=payload)
    if response.is_success:
        return CheckResult("Gemini", True, f"HTTP {response.status_code}")
    return CheckResult("Gemini", False, f"HTTP {response.status_code}: {response.text[:160]}")


async def check_ollama() -> CheckResult:
    settings = get_settings()
    url = f"{settings.ollama_base_url}/api/tags"
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(url)
    if response.is_success:
        models = response.json().get("models", [])
        return CheckResult("Ollama", True, f"HTTP {response.status_code}, models={len(models)}")
    return CheckResult("Ollama", False, f"HTTP {response.status_code}: {response.text[:160]}")


async def check_openrouter(api_key: str, label: str) -> CheckResult:
    settings = get_settings()
    if not api_key:
        return CheckResult(label, False, f"{label} env key eksik.")
    url = f"{settings.openrouter_base_url}/key"
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(url, headers=headers)
    if response.is_success:
        limit_remaining = response.json().get("data", {}).get("limit_remaining", "unknown")
        return CheckResult(label, True, f"HTTP {response.status_code}, limit_remaining={limit_remaining}")
    return CheckResult(label, False, f"HTTP {response.status_code}: {response.text[:160]}")


async def check_sqlite_saver() -> CheckResult:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    repository = Repository()
    await repository.initialize()

    async with AsyncSqliteSaver.from_conn_string(str(settings.graph_checkpoint_path)) as saver:
        config = {"configurable": {"thread_id": f"{settings.graph_thread_prefix}-checkpoint"}}
        checkpoint = {"v": 1, "ts": "phase1", "id": "phase1", "channel_values": {"status": "ok"}, "channel_versions": {}, "versions_seen": {}}
        metadata: dict[str, Any] = {"source": "smoke-test"}
        await saver.aput(config=config, checkpoint=checkpoint, metadata=metadata, new_versions={})
        saved = await saver.aget_tuple(config)
    if saved is None:
        return CheckResult("SqliteSaver", False, "Checkpoint okunamadi.")
    return CheckResult("SqliteSaver", True, "Checkpoint yazildi ve geri okundu.")


async def check_graph_flow() -> CheckResult:
    result = await run_minimal_graph()
    messages = result["result"].get("messages", [])
    checkpoint_values = result["checkpoint_values"]
    expected_steps = {"planner completed", "worker completed", "reviewer completed"}
    if expected_steps.issubset(set(messages)) and checkpoint_values.get("sprint_status") == "completed":
        return CheckResult(
            "LangGraph Flow",
            True,
            f"thread_id={result['thread_id']}, next={result['checkpoint_next']}",
        )
    return CheckResult("LangGraph Flow", False, f"Beklenen akis tamamlmadi: {messages}")


async def run_checks() -> list[CheckResult]:
    checks = [
        check_gemini(),
        check_ollama(),
        check_openrouter(get_settings().openrouter_api_key_primary, "OpenRouter Primary"),
        check_openrouter(get_settings().openrouter_api_key_secondary, "OpenRouter Secondary"),
        check_sqlite_saver(),
        check_graph_flow(),
    ]
    results = await asyncio.gather(*checks, return_exceptions=True)
    normalized: list[CheckResult] = []
    for item in results:
        if isinstance(item, Exception):
            normalized.append(CheckResult("Unexpected", False, str(item)))
        else:
            normalized.append(item)
    return normalized


def main() -> None:
    configure_logging()
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")


if __name__ == "__main__":
    main()
