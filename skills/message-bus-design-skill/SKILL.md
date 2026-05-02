---
name: message-bus-design
description: Coder AI için — EventBus'un pub/sub mesaj iletimini tasarlamak ve implemente etmek; topic tabanlı mesajlaşma, handler kayıt ve async dispatch.
---

## Purpose

Telegram handler ve LangGraph node'ları doğrudan birbirine bağlanmamalı.
EventBus aralarındaki köprüdür — bağımlılıkları azaltır.
Topic bazlı routing: `user.approval`, `sprint.done`, `worker.failed`.

---

## When to Apply

- `src/core/event_bus.py` yazılırken
- Yeni event tipi eklenirken
- Bileşenler arası iletişim tasarlanırken

---

## Rules

- Topic: `namespace.event_name` formatı (noktalı).
- Handler: `async def handler(payload: dict) -> None`.
- Hata: handler exception'ı diğer handler'ları durdurmaz.
- Singleton: tek EventBus instance.
- Handler kayıt: `subscribe(topic, handler)`.

---

## Guidelines

```python
# src/core/event_bus.py
from typing import Callable, Awaitable

HandlerType = Callable[[dict], Awaitable[None]]

class EventBus:
    _instance: "EventBus | None" = None
    
    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers: dict[str, list[HandlerType]] = {}
        return cls._instance
    
    def subscribe(self, topic: str, handler: HandlerType) -> None:
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)
        logger.debug(f"Handler kayıtlı: {topic}")
    
    def unsubscribe(self, topic: str, handler: HandlerType) -> None:
        if topic in self._handlers:
            self._handlers[topic].discard(handler)
    
    async def emit(self, topic: str, payload: dict) -> None:
        handlers = self._handlers.get(topic, [])
        if not handlers:
            logger.debug(f"Event işlenmedi (handler yok): {topic}")
            return
        
        tasks = [
            asyncio.create_task(_safe_call(h, payload))
            for h in handlers
        ]
        await asyncio.gather(*tasks)
    
    @classmethod
    def reset(cls) -> None:
        cls._instance = None

async def _safe_call(handler: HandlerType, payload: dict) -> None:
    try:
        await handler(payload)
    except Exception as e:
        logger.error(f"Event handler hatası: {e}")

# Tanımlı event topic'leri
class Topics:
    USER_APPROVAL     = "user.approval"
    SPRINT_DONE       = "sprint.done"
    SPRINT_FAILED     = "sprint.failed"
    WORKER_COMPLETED  = "worker.completed"
    WORKER_FAILED     = "worker.failed"
    STATUS_REQUESTED  = "telegram.status_requested"
```

---

## References

- `event-emission-pattern-skill/SKILL.md` — event emit
- `event-subscription-pattern-skill/SKILL.md` — event subscribe
- `mock-event-bus-skill/SKILL.md` — test mock
