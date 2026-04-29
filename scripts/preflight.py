from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

import aiofiles
import aiofiles.os
import aiofiles.ospath
import aiosqlite
import httpx

from src.config.settings import get_settings


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


async def check_environment() -> CheckResult:
    settings = get_settings()
    required = {
        "APP_NAME": settings.app_name,
        "DATA_DIR": str(settings.data_dir),
        "PROJECTS_ROOT": str(settings.projects_root),
        "SQLITE_DB_PATH": str(settings.sqlite_db_path),
        "GRAPH_CHECKPOINT_PATH": str(settings.graph_checkpoint_path),
        "OLLAMA_BASE_URL": settings.ollama_base_url,
        "OLLAMA_MODEL": settings.ollama_model,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        return CheckResult("Environment", False, f"Eksik zorunlu ayarlar: {', '.join(missing)}")
    return CheckResult("Environment", True, "Zorunlu daemon/runtime ayarlari mevcut.")


async def check_provider_access() -> CheckResult:
    settings = get_settings()
    details: list[str] = []
    passed = True
    timeout = httpx.Timeout(settings.http_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
            models = {item.get("model") for item in payload.get("models", []) if isinstance(item, dict)}
            if settings.ollama_model in models:
                details.append("Ollama=PASS")
            else:
                passed = False
                details.append(f"Ollama=FAIL(model_missing:{settings.ollama_model})")
        except Exception as exc:  # noqa: BLE001
            passed = False
            details.append(f"Ollama=FAIL({type(exc).__name__})")

    if settings.gemini_api_key:
        details.append("Gemini=PASS(configured)")
    else:
        details.append("Gemini=PASS(disabled)")
    if settings.openrouter_api_key_primary or settings.openrouter_api_key_secondary:
        details.append("OpenRouter=PASS(configured)")
    else:
        details.append("OpenRouter=PASS(disabled)")
    return CheckResult("Providers", passed, " | ".join(details))


async def check_storage_permissions() -> CheckResult:
    settings = get_settings()
    await aiofiles.os.makedirs(settings.data_dir, exist_ok=True)
    await aiofiles.os.makedirs(settings.projects_root, exist_ok=True)
    test_files = [settings.sqlite_db_path, settings.graph_checkpoint_path, settings.state_snapshot_path]
    for path in test_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "a", encoding="utf-8") as handle:
            await handle.write("")
    try:
        async with aiosqlite.connect(settings.sqlite_db_path) as connection:
            await connection.execute("CREATE TABLE IF NOT EXISTS preflight_probe (id INTEGER PRIMARY KEY)")
            await connection.commit()
        async with aiosqlite.connect(settings.graph_checkpoint_path) as connection:
            await connection.execute("CREATE TABLE IF NOT EXISTS checkpoint_probe (id INTEGER PRIMARY KEY)")
            await connection.commit()
    except Exception as exc:  # noqa: BLE001
        return CheckResult("Storage", False, f"Sqlite/checkpoint yazma izni yok: {type(exc).__name__}: {exc}")
    return CheckResult("Storage", True, "Sqlite, checkpoint ve snapshot path'leri yazilabilir.")


async def check_telegram_settings() -> CheckResult:
    settings = get_settings()
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id
    if not token and not chat_id:
        return CheckResult("Telegram", True, "Telegram entegrasyonu devre disi.")
    if not token or not chat_id:
        return CheckResult("Telegram", False, "Telegram token/chat id ciftinden biri eksik.")
    return CheckResult("Telegram", True, "Telegram token ve yetkili chat id birlikte tanimli.")


async def check_systemd_unit() -> CheckResult:
    service_path = Path("ai-orchestrator.service")
    if not service_path.exists():
        return CheckResult("Systemd Unit", False, "ai-orchestrator.service bulunamadi.")
    content = service_path.read_text(encoding="utf-8")
    required_bits = ["ExecStart=", "EnvironmentFile=", "WorkingDirectory=", "Restart=on-failure", "TimeoutStopSec="]
    missing = [bit for bit in required_bits if bit not in content]
    if missing:
        return CheckResult("Systemd Unit", False, f"Unit icinde eksik alanlar: {', '.join(missing)}")
    return CheckResult("Systemd Unit", True, "Systemd unit temel path ve restart ayarlariyla uyumlu.")


async def run_checks() -> list[CheckResult]:
    return [
        await check_environment(),
        await check_provider_access(),
        await check_storage_permissions(),
        await check_telegram_settings(),
        await check_systemd_unit(),
    ]


def print_summary(results: list[CheckResult]) -> None:
    pass_count = sum(1 for result in results if result.passed)
    fail_count = len(results) - pass_count
    print("\n=== PREFLIGHT SUMMARY ===")
    print(f"TOTAL: {len(results)}")
    print(f"PASS: {pass_count}")
    print(f"FAIL: {fail_count}")
    if fail_count:
        print("FAIL_REASONS:")
        for item in results:
            if not item.passed:
                print(f"- {item.name}: {item.detail}")
    else:
        print("FAIL_REASONS: none")
    print(f"PREFLIGHT_STATUS: {'PASS' if fail_count == 0 else 'FAIL'}")


def main() -> None:
    results = asyncio.run(run_checks())
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
    print_summary(results)


if __name__ == "__main__":
    main()
