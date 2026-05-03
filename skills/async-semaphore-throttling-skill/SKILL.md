---
name: async-semaphore-throttling
description: Coder AI için — asyncio.Semaphore ile eşzamanlı işlem sayısını sınırlamak; kaynakları aşırı yüklemeden paralel iş yapmak.
---

## Purpose

Sınırsız paralel LLM çağrısı rate limit'e çarpar.
Semaphore: aynı anda en fazla N çağrı — fazlası sırada bekler.
Worker pool veya API client için temel throttling mekanizması.

---

## When to Apply

- Paralel LLM çağrıları yapılırken (maks 3 eşzamanlı)
- DB bağlantı havuzunu korurken
- Harici API'ye saniyede maks N istek gönderilirken

---

## Rules

- Semaphore değeri: `MAX_CONCURRENT_WORKERS` config'den gelir.
- Her `acquire`: otomatik `release` için `async with` kullan.
- Semaphore global — tüm worker'lar paylaşır.
- Timeout: 30s bekledikten sonra hata fırlat.

---

## Guidelines

```python
import asyncio
from typing import Any, Callable, Awaitable

_llm_semaphore: asyncio.Semaphore | None = None

def get_llm_semaphore(max_concurrent: int = 3) -> asyncio.Semaphore:
    global _llm_semaphore
    if _llm_semaphore is None:
        _llm_semaphore = asyncio.Semaphore(max_concurrent)
    return _llm_semaphore

async def throttled_llm_call(
    llm,
    messages: list,
    max_concurrent: int = 3,
    timeout: float = 30.0,
) -> Any:
    sem = get_llm_semaphore(max_concurrent)
    
    try:
        async with asyncio.timeout(timeout):
            async with sem:
                return await llm.ainvoke(messages)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Semaphore bekleme süresi aşıldı ({timeout}s)")

async def map_with_throttle(
    items: list,
    fn: Callable[..., Awaitable[Any]],
    max_concurrent: int = 3,
) -> list:
    sem = asyncio.Semaphore(max_concurrent)
    
    async def bounded(item):
        async with sem:
            return await fn(item)
    
    return await asyncio.gather(*[bounded(item) for item in items], return_exceptions=True)

# Kullanım örneği
async def process_files_throttled(files: list[str], worker_fn) -> list:
    return await map_with_throttle(files, worker_fn, max_concurrent=3)
```

---

## References

- `worker-concurrency-control-skill/SKILL.md` — eşzamanlılık kontrolü
- `async-lock-usage-skill/SKILL.md` — async kilit
- `api-rate-limit-handling-skill/SKILL.md` — API hız limiti
