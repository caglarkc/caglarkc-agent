---
name: python-async-patterns
description: AI Development Team Orchestrator projesinde kullanılan Python async pattern'ları. EventBus tasarımı, asyncio kuralları, daemon yapısı, concurrent task yönetimi, crash recovery. Async kod yazarken veya review ederken referans alınır.
---

## Temel Kurallar

- Tüm I/O işlemleri `async/await` ile yazılır
- `requests`, `time.sleep` gibi blocking call'lar yasak — `httpx`, `asyncio.sleep` kullan
- `asyncio.run()` sadece `main.py`'de, entry point'te kullanılır
- Paralel işlemler `asyncio.gather()` ile yapılır
- Her async fonksiyon `await` içerir — boş async fonksiyon yazılmaz

---

## EventBus

Telegram ve CLI'ı senkron tutan merkezi event sistemi:

```python
# src/core/event_bus.py
import asyncio
from typing import Callable, Any
from collections import defaultdict

class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = defaultdict(list)
        return cls._instance

    def subscribe(self, event: str, callback: Callable) -> None:
        self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable) -> None:
        self._subscribers[event].remove(callback)

    async def emit(self, event: str, data: Any = None) -> None:
        tasks = [
            asyncio.create_task(callback(data))
            for callback in self._subscribers[event]
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Kullanım
bus = EventBus()

# Telegram dinler
bus.subscribe("sprint.completed", telegram_notifier.on_sprint_completed)

# CLI dinler
bus.subscribe("sprint.completed", cli_notifier.on_sprint_completed)

# CrewAI emit eder
await bus.emit("sprint.completed", {"sprint_id": "...", "summary": "..."})
```

---

## Daemon Yapısı

```python
# main.py
import asyncio
import signal
from src.core.event_bus import EventBus
from src.interfaces.telegram.bot import TelegramBot
from src.interfaces.cli.app import CLIApp
from src.crew.flow import OrchestratorFlow

async def main():
    # Bileşenleri başlat
    bus = EventBus()
    telegram = TelegramBot()
    flow = OrchestratorFlow()

    # Graceful shutdown için signal handler
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    # Paralel başlat
    await asyncio.gather(
        telegram.start(),
        flow.listen(),        # Event bekler
        keep_alive()          # Daemon loop
    )

async def keep_alive():
    while True:
        await asyncio.sleep(60)

async def shutdown():
    # Temiz kapatma
    await telegram.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Concurrent Task Yönetimi

```python
# Paralel worker başlatma
async def run_sprint_parallel(worker_tasks: list[dict]) -> list:
    results = await asyncio.gather(
        *[run_worker(task) for task in worker_tasks],
        return_exceptions=True
    )

    # Hataları ayır
    errors = [r for r in results if isinstance(r, Exception)]
    successes = [r for r in results if not isinstance(r, Exception)]

    return successes, errors

# Timeout ile çalıştırma
async def run_with_timeout(coro, timeout: int = 300):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise WorkerTimeoutError(f"Worker {timeout}s içinde tamamlayamadı")
```

---

## Retry Pattern

```python
import asyncio
from functools import wraps

def async_retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator

# Kullanım
@async_retry(max_attempts=3, delay=2.0)
async def call_openrouter(prompt: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={"prompt": prompt})
        return response.json()
```

---

## State Yönetimi (Async-safe)

```python
# src/core/state_manager.py
import asyncio
from typing import Any

class StateManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._state = {}
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._state[key] = value

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._state.get(key, default)

    async def update(self, key: str, updates: dict) -> None:
        async with self._lock:
            if key in self._state:
                self._state[key].update(updates)
```

---

## Crash Recovery

CrewAI Flow SQLite persistence ile kaldığı yerden devam eder:

```python
from crewai.flow.persistence.sqlite import SQLiteFlowPersistence

persistence = SQLiteFlowPersistence(db_path="./storage/flow_state.db")

# Flow başlatırken persistence ver
flow = OrchestratorFlow(persistence=persistence)

# Crash sonrası resume:
async def recover_pending_flows():
    pending = await persistence.get_all_pending()
    for flow_state in pending:
        flow = OrchestratorFlow.from_pending(
            flow_id=flow_state.flow_id,
            persistence=persistence
        )
        asyncio.create_task(flow.resume())
```

---

## Logging

```python
import logging
import asyncio
from rich.logging import RichHandler

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True),
            logging.FileHandler("logs/orchestrator.log")
        ]
    )

logger = logging.getLogger("orchestrator")

# Async context'te kullanım
async def some_function():
    logger.info("Sprint başladı", extra={"sprint_id": "..."})
    try:
        result = await do_work()
    except Exception as e:
        logger.error(f"Sprint hatası: {e}", exc_info=True)
        raise
```