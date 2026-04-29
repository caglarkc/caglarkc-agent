from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import warnings
from pathlib import Path
from uuid import uuid4

import aiofiles.os
from langchain_community.chat_models import ChatOllama
from langchain_community.llms.ollama import OllamaEndpointNotFoundError
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.types import Command

from src.config.logging_config import configure_logging
from src.config.settings import get_settings
from src.graph.graph import build_thread_config, graph_runtime
from src.graph.state import build_initial_state
from src.storage.repository import Repository

LOGGER = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def _clean_detail(detail: str) -> str:
    normalized = " ".join(detail.strip().split())
    return normalized[:240]


def _exception_detail(error: Exception) -> str:
    return _clean_detail(f"{type(error).__name__}: {error}")


async def check_gemini() -> CheckResult:
    settings = get_settings()
    if not settings.gemini_api_key:
        return CheckResult("Gemini", False, "GEMINI_API_KEY eksik.")
    try:
        model = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            timeout=settings.http_timeout_seconds,
            temperature=0,
        )
        response = await model.ainvoke("Ping")
    except Exception as error:
        return CheckResult("Gemini", False, _exception_detail(error))
    content = _clean_detail(str(response.content))
    return CheckResult("Gemini", True, f"LangChain adapter yanit verdi: {content or 'bos-icerik'}")


async def check_ollama() -> CheckResult:
    settings = get_settings()
    try:
        model = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
        response = await model.ainvoke("Ping")
    except OllamaEndpointNotFoundError as error:
        return CheckResult(
            "Ollama",
            False,
            _clean_detail(
                f"Ollama inference endpoint bulunamadi veya bu host generate/chat endpoint'i sunmuyor: {error}"
            ),
        )
    except Exception as error:
        return CheckResult("Ollama", False, _exception_detail(error))
    content = _clean_detail(str(response.content))
    return CheckResult("Ollama", True, f"LangChain adapter yanit verdi: {content or 'bos-icerik'}")


async def check_openrouter(api_key: str, label: str, model_name: str) -> CheckResult:
    settings = get_settings()
    if not api_key:
        return CheckResult(label, False, f"{label} env key eksik.")
    try:
        model = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=settings.openrouter_base_url,
            temperature=0,
            timeout=settings.http_timeout_seconds,
            default_headers={
                "HTTP-Referer": "https://local.phase1.smoke",
                "X-Title": "AI Development Team Orchestrator",
            },
        )
        response = await model.ainvoke("Ping")
    except Exception as error:
        return CheckResult(label, False, _exception_detail(error))
    content = _clean_detail(str(response.content))
    return CheckResult(label, True, f"LangChain adapter yanit verdi: {content or 'bos-icerik'}")


async def run_minimal_graph() -> dict:
    """Plan onayı → dispatcher’dan sonra tüm düğümler tek smoke akışında (ayrı checkpoint dosyası)."""
    settings = get_settings()
    thread_id = f"chk-{uuid4().hex[:12]}"
    checkpoint_path = Path(settings.data_dir) / "check_connections_graph.sqlite"

    async with graph_runtime(checkpoint_path) as graph:
        config = build_thread_config(thread_id)
        initial = build_initial_state(
            project_name="phase1-connection-smoke",
            task_description="connection smoke minimal run",
            current_thread_id=thread_id,
        )
        paused = await graph.ainvoke(initial, config=config)
        snapshot = await graph.aget_state(config)
        values_before = snapshot.values
        if not values_before.get("awaiting_approval"):
            return {
                "thread_id": thread_id,
                "result": paused,
                "checkpoint_values": {},
                "checkpoint_next": [],
            }

        await graph.aupdate_state(
            config,
            {
                "awaiting_approval": False,
                "approval_type": "",
                "active_approval_id": None,
                "approval_request": None,
                "messages": [*values_before.get("messages", []), "smoke:auto-approved plan"],
            },
            as_node="planner",
        )
        final_state = await graph.ainvoke(Command(goto="dispatcher"), config=config)
        refreshed = await graph.aget_state(config)
        chk = dict(refreshed.values)
        return {
            "thread_id": thread_id,
            "result": final_state if isinstance(final_state, dict) else chk,
            "checkpoint_values": chk,
            "checkpoint_next": list(refreshed.next),
        }


def _messages_indicate_complete(messages: list) -> tuple[bool, str]:
    msgs = [str(m) for m in messages] if isinstance(messages, list) else []
    blob = "\n".join(msgs)
    need = []
    if "planner completed" not in blob:
        need.append("planner")
    if not any("worker completed" in m for m in msgs):
        need.append("worker")
    if "validator completed" not in blob:
        need.append("validator")
    if "reviewer approved sprint" not in blob:
        need.append("reviewer")
    return (not need), ", eksik:" + ",".join(need) if need else ""


async def check_graph_and_checkpoint() -> tuple[CheckResult, CheckResult]:
    settings = get_settings()
    await aiofiles.os.makedirs(settings.data_dir, exist_ok=True)
    repository = Repository()
    await repository.initialize()

    result = await run_minimal_graph()
    if not result["checkpoint_values"]:
        checkpoint_result = CheckResult("SqliteSaver", False, "Checkpoint okunamadi.")
    else:
        checkpoint_result = CheckResult(
            "SqliteSaver",
            True,
            f"Checkpoint yazildi ve geri okundu: {result['thread_id']}",
        )
    checkpoint_values = result["checkpoint_values"]
    messages = checkpoint_values.get("messages") or []
    ok_msgs, diag = _messages_indicate_complete(messages)
    status_ok = checkpoint_values.get("sprint_status") == "approved"
    if ok_msgs and status_ok:
        graph_result = CheckResult(
            "LangGraph Flow",
            True,
            f"thread_id={result['thread_id']}, next={result['checkpoint_next']}",
        )
    else:
        graph_result = CheckResult(
            "LangGraph Flow",
            False,
            f"sprint_status={checkpoint_values.get('sprint_status')}{diag}; messages={messages[-8:]}",
        )
    return checkpoint_result, graph_result


async def run_checks() -> list[CheckResult]:
    settings = get_settings()
    results: list[CheckResult] = []
    checks = [
        ("Gemini", check_gemini),
        ("Ollama", check_ollama),
        (
            "OpenRouter Primary",
            lambda: check_openrouter(
                settings.openrouter_api_key_primary,
                "OpenRouter Primary",
                settings.openrouter_model,
            ),
        ),
        (
            "OpenRouter Secondary",
            lambda: check_openrouter(
                settings.openrouter_api_key_secondary,
                "OpenRouter Secondary",
                settings.openrouter_model_secondary,
            ),
        ),
    ]

    for name, check in checks:
        LOGGER.info("Baglanti kontrolu basliyor: %s", name)
        try:
            results.append(await check())
        except Exception as error:
            results.append(CheckResult(name, False, _exception_detail(error)))

    LOGGER.info("Checkpoint ve graph smoke testleri seri olarak calistiriliyor.")
    try:
        checkpoint_result, graph_result = await check_graph_and_checkpoint()
        results.extend([checkpoint_result, graph_result])
    except Exception as error:
        detail = _exception_detail(error)
        results.append(CheckResult("SqliteSaver", False, detail))
        results.append(CheckResult("LangGraph Flow", False, detail))

    return results


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for item in results if item.passed)
    fail_count = len(results) - pass_count
    failed_items = [item for item in results if not item.passed]
    phase_status = "READY" if fail_count == 0 else "NOT_READY"

    print("\n=== PHASE 1 ACCEPTANCE SUMMARY ===")
    print(f"TOTAL_CHECKS: {len(results)}")
    print(f"PASS: {pass_count}")
    print(f"FAIL: {fail_count}")
    if failed_items:
        print("FAIL_REASONS:")
        for item in failed_items:
            print(f"- {item.name}: {item.detail}")
    else:
        print("FAIL_REASONS: none")
    print(f"PHASE_1_STATUS: {phase_status}")


def main() -> None:
    configure_logging()
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
