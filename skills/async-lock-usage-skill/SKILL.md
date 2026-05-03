---
name: async-lock-usage
description: Coder AI için — asyncio.Lock ile paylaşılan kaynakları korumak; eşzamanlı erişimde yarış koşullarını önlemek.
---

## Purpose

Birden fazla coroutine aynı state'i okuyup yazarsa veri bozulur.
asyncio.Lock: kritik bölgeye aynı anda tek coroutine girer.
Async ortamda threading.Lock yerine asyncio.Lock kullanılmalı.

---

## When to Apply

- `file_registry` veya `worker_registry` güncellenirken
- Sayaç artırımı gibi okuma-yazma operasyonlarında
- Shared resource'a birden fazla coroutine eriştiğinde

---

## Rules

- Lock: modül seviyesinde tek örnek (singleton).
- `async with lock:` — elle acquire/release değil.
- Deadlock: lock içinde başka lock bekleme.
- Timeout: `asyncio.wait_for` ile lock alma süresi sınırlanır.

---

## Guidelines

```python
import asyncio

# Paylaşılan kaynak başına bir lock
_file_registry_lock = asyncio.Lock()
_worker_registry_lock = asyncio.Lock()

async def update_file_status(
    state: dict,
    file_path: str,
    new_status: str,
) -> dict:
    async with _file_registry_lock:
        registry = dict(state.get("file_registry", {}))
        registry[file_path] = new_status
        return {"file_registry": registry}

async def increment_counter(state: dict, key: str) -> dict:
    async with _file_registry_lock:
        current = state.get(key, 0)
        return {key: current + 1}

# Lock alma timeout ile
async def safe_acquire(lock: asyncio.Lock, timeout: float = 5.0) -> bool:
    try:
        await asyncio.wait_for(lock.acquire(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False

# RLock yoktur asyncio'da — reentrant lock gerekirse semaphore ile simüle
_semaphore = asyncio.Semaphore(1)

async def with_semaphore(coro):
    async with _semaphore:
        return await coro
```

---

## References

- `worker-concurrency-control-skill/SKILL.md` — eşzamanlılık kontrolü
- `file-write-atomicity-skill/SKILL.md` — atomik yazma
- `async-context-manager-skill/SKILL.md` — async context manager
