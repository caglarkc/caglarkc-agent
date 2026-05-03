---
name: async-event-driven
description: Coder AI için — asyncio event loop üzerinde olay güdümlü mimari kurmak; callback yerine async event handler kullanmak.
---

## Purpose

Senkron callback'ler async sistemde bloklamaya yol açar.
Async event handler: await destekler, I/O beklerken loop serbest kalır.
EventBus ile loosely coupled bileşenler birbirini doğrudan çağırmaz.

---

## When to Apply

- EventBus subscriber'ları async işlem yapacaksa
- LangGraph node'u bir eventi dinleyip tepki verecekse
- Birden fazla handler aynı eventi işleyecekse

---

## Rules

- Handler: `async def` olmalı.
- İstisna: handler içindeki hata diğer handler'ları etkilemez.
- Handler süresi: 30 saniyeyi geçmemeli (timeout ile sarılır).
- Sıra garantisi yok — bağımsız handler'lar paralel çalışabilir.

---

## Guidelines

```python
import asyncio
from collections import defaultdict
from typing import Callable, Awaitable

HandlerFn = Callable[[dict], Awaitable[None]]

class AsyncEventBus:
    def __init__(self):
        self._handlers: dict[str, list[HandlerFn]] = defaultdict(list)
    
    def subscribe(self, event: str, handler: HandlerFn) -> None:
        self._handlers[event].append(handler)
    
    async def publish(self, event: str, payload: dict) -> None:
        handlers = self._handlers.get(event, [])
        if not handlers:
            return
        results = await asyncio.gather(
            *[self._safe_call(h, payload) for h in handlers],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                import logging
                logging.getLogger(__name__).error(
                    "Event handler hatası [%s]: %s", event, r
                )
    
    async def _safe_call(self, handler: HandlerFn, payload: dict) -> None:
        await asyncio.wait_for(handler(payload), timeout=30.0)

# Kullanım örneği
bus = AsyncEventBus()

@bus.subscribe("sprint.completed")  # Decorator değil — elle ekleme
async def on_sprint_completed(payload: dict) -> None:
    sprint_id = payload["sprint_id"]
    # Bildirim gönder, DB güncelle vb.
    await notify_user(sprint_id)

bus.subscribe("sprint.completed", on_sprint_completed)
```

---

## References

- `event-replay-skill/SKILL.md` — event tekrar oynatma
- `message-bus-design-skill/SKILL.md` — mesaj otobüsü tasarımı
- `notification-abstraction-skill/SKILL.md` — bildirim soyutlama
