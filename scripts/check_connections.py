from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import warnings

import aiofiles.os
from langchain_community.chat_models import ChatOllama
from langchain_community.llms.ollama import OllamaEndpointNotFoundError
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.config.logging_config import configure_logging
from src.config.settings import get_settings
from src.graph.graph import run_minimal_graph
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


async def check_openrouter(api_key: str, label: str) -> CheckResult:
    settings = get_settings()
    if not api_key:
        return CheckResult(label, False, f"{label} env key eksik.")
    try:
        model = ChatOpenAI(
            model=settings.openrouter_model,
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
    messages = result["result"].get("messages", [])
    checkpoint_values = result["checkpoint_values"]
    expected_steps = {"planner completed", "worker completed", "reviewer completed"}
    if expected_steps.issubset(set(messages)) and checkpoint_values.get("sprint_status") == "completed":
        graph_result = CheckResult(
            "LangGraph Flow",
            True,
            f"thread_id={result['thread_id']}, next={result['checkpoint_next']}",
        )
    else:
        graph_result = CheckResult(
            "LangGraph Flow",
            False,
            f"Beklenen akis tamamlanmadi: {messages}",
        )
    return checkpoint_result, graph_result


async def run_checks() -> list[CheckResult]:
    settings = get_settings()
    results: list[CheckResult] = []
    checks = [
        ("Gemini", check_gemini),
        ("Ollama", check_ollama),
        ("OpenRouter Primary", lambda: check_openrouter(settings.openrouter_api_key_primary, "OpenRouter Primary")),
        ("OpenRouter Secondary", lambda: check_openrouter(settings.openrouter_api_key_secondary, "OpenRouter Secondary")),
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
