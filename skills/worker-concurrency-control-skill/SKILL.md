---
name: worker-concurrency-control
description: Coder AI için — paralel çalışan worker sayısını asyncio.Semaphore ile sınırlamak; sistem kaynaklarını aşırı yüklemeden korumak.
---

## Purpose

Sınırsız paralel worker bellek ve LLM rate limit sorunlarına yol açar.
Semaphore, eş zamanlı worker sayısını sabit bir limite kilitler.
Yeni worker başlamak için mevcut bir worker'ın bitmesi beklenir.

---

## When to Apply

- Executor node paralel worker başlatırken
- `asyncio.gather` yerine kontrollü paralel çalışma yapılırken
- Rate limit ile karşılaşıldığında backpressure eklenirken

---

## Rules

- `MAX_CONCURRENT_WORKERS = 3` varsayılan.
- Semaphore: modül düzeyinde singleton veya executor'a inject edilir.
- Semaphore `async with` bloğu içinde kullanılır.
- Semaphore timeout: 60 saniye (takılı kalan worker'ı kurtarır).

---

## Guidelines

```python
import asyncio
from contextlib import asynccontextmanager

class ConcurrencyController:
    def __init__(self, max_workers: int = 3):
        self._sem = asyncio.Semaphore(max_workers)
        self._max = max_workers
        self._active = 0
    
    @asynccontextmanager
    async def worker_slot(self, timeout: float = 60.0):
        try:
            await asyncio.wait_for(self._sem.acquire(), timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Semaphore timeout: {timeout}s içinde slot alınamadı"
            )
        self._active += 1
        try:
            yield
        finally:
            self._active -= 1
            self._sem.release()
    
    @property
    def active_count(self) -> int:
        return self._active

# Executor'da kullanım
controller = ConcurrencyController(max_workers=3)

async def run_controlled_workers(entries: list[QueueEntry]) -> list:
    results = []
    
    async def run_one(entry: QueueEntry) -> dict:
        async with controller.worker_slot(timeout=60.0):
            return await worker_node(state, entry)
    
    # Tüm task'ları başlat — semaphore max_workers'ı aşmayı engeller
    tasks = [asyncio.create_task(run_one(e)) for e in entries]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for entry, result in zip(entries, raw_results):
        if isinstance(result, Exception):
            logger.error(f"Worker hata: {entry.file_path}: {result}")
        else:
            results.append(result)
    
    return results
```

---

## References

- `executor-node-implementation-skill/SKILL.md` — executor
- `worker-status-tracking-skill/SKILL.md` — worker takibi
- `asyncio-lock-usage-skill/SKILL.md` — lock kullanımı
