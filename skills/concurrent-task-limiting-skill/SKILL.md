---
name: concurrent-task-limiting
description: Coder AI için — asyncio.Semaphore ve asyncio.BoundedSemaphore ile eşzamanlı görev sayısını sınırlamak; kaynak tüketimini kontrol altında tutmak.
---

## Purpose

Sınırsız eşzamanlı görev sistem belleğini tüketir.
`BoundedSemaphore` semaphore sınırının aşılmasını da önler.
Rate limit koruması için LLM çağrıları da sınırlandırılabilir.

---

## When to Apply

- Paralel worker sayısı sınırlanırken
- LLM API rate limit koruması eklenirken
- DB bağlantı havuzu yönetilirken

---

## Rules

- `asyncio.Semaphore(N)`: N eşzamanlı işlem.
- `asyncio.BoundedSemaphore(N)`: fazla release() fırlatır — güvenlik.
- Timeout: `asyncio.wait_for` ile semaphore bekleme süresi sınırlanır.
- Her release() garantili: `try/finally` veya async context manager.

---

## Guidelines

```python
import asyncio

class RateLimiter:
    """Belirli periyotta max N çağrıya izin verir."""
    
    def __init__(self, max_calls: int, period: float):
        self._sem = asyncio.Semaphore(max_calls)
        self._period = period
        self._max = max_calls
    
    async def __aenter__(self):
        await self._sem.acquire()
        return self
    
    async def __aexit__(self, *args):
        # Periyot sonunda release
        asyncio.get_event_loop().call_later(
            self._period, self._sem.release
        )

# LLM rate limiting (dakikada 10 çağrı)
llm_rate_limiter = RateLimiter(max_calls=10, period=60.0)

async def rate_limited_llm_invoke(llm, messages):
    async with llm_rate_limiter:
        return await llm.ainvoke(messages)

# DB bağlantı havuzu simülasyonu
DB_POOL_LIMIT = 5
db_semaphore = asyncio.BoundedSemaphore(DB_POOL_LIMIT)

async def get_db_connection(db_path: str):
    async with db_semaphore:
        async with aiosqlite.connect(db_path) as conn:
            yield conn

# Worker sayısı sınırlama (basit)
MAX_WORKERS = 3
worker_semaphore = asyncio.Semaphore(MAX_WORKERS)

async def run_worker_with_limit(entry: QueueEntry) -> dict:
    async with worker_semaphore:
        return await execute_worker(entry)
```

---

## References

- `worker-concurrency-control-skill/SKILL.md` — worker sınırlama
- `asyncio-lock-usage-skill/SKILL.md` — lock kullanımı
- `rate-limit-handling-skill/SKILL.md` — rate limit
