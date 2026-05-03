---
name: code-generator-function
description: Coder AI için — Python generator fonksiyonları ile büyük veri setlerini bellek dostu şekilde işlemek.
---

## Purpose

Büyük liste döndüren fonksiyon tüm veriyi belleğe yükler.
Generator: `yield` ile değerleri birer birer üretir — bellek sabit kalır.
LangGraph state geçmişi, log satırları, dosya listesi için ideal.

---

## When to Apply

- Büyük koleksiyon üzerinde iterasyon yapılırken
- Streaming yanıt chunk'ları işlenirken
- Tembel (lazy) değerlendirme gereken her yerde

---

## Rules

- Generator fonksiyon: `return` yerine `yield`.
- Async generator: `async def` + `yield` + `async for`.
- Cleanup: `try/finally` içinde `yield` (context manager benzeri).
- `list()` ile zorla: sadece tüm değer gerektiğinde.

---

## Guidelines

```python
from typing import Generator, AsyncGenerator

# Sync generator
def read_audit_log_lazy(log_path: str) -> Generator[dict, None, None]:
    import json
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line.strip())
            except json.JSONDecodeError:
                continue

# Async generator
async def stream_sprint_events(
    event_bus,
    sprint_id: str,
    timeout: float = 300.0,
) -> AsyncGenerator[dict, None]:
    import asyncio
    queue: asyncio.Queue[dict] = asyncio.Queue()

    async def handler(topic: str, payload: dict) -> None:
        if payload.get("sprint_id") == sprint_id:
            await queue.put(payload)

    event_bus.subscribe("sprint.*", handler)
    try:
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=remaining)
                yield event
            except asyncio.TimeoutError:
                break
    finally:
        event_bus.unsubscribe("sprint.*", handler)

# Pipeline: generator zinciri
def filter_done(events):
    return (e for e in events if e.get("status") == "done")

def extract_files(events):
    return (e.get("file_path") for e in events if e.get("file_path"))
```

---

## References

- `async-generator-pattern-skill/SKILL.md` — async generator
- `streaming-response-handling-skill/SKILL.md` — streaming yanıt
- `batch-processing-skill/SKILL.md` — toplu işleme
