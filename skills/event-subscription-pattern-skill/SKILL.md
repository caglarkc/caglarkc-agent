---
name: event-subscription-pattern
description: Coder AI için — EventBus'a abone olmanın standart yolu; callback kayıt, async callback, ve subscription lifecycle yönetimi.
---

## Purpose

Event listener'ların doğru şekilde kayıt edilmesini sağlar.
Async callback'ler için doğru signature kullanılır.
Subscription lifecycle (başlangıç/bitiş) doğru yönetilir.

---

## When to Apply

- Interface bileşeni (CLI, Telegram) event'leri dinleyecekse
- GraphManager plan event'lerini yakalayacaksa
- Yeni event handler yazılırken

---

## Rules

- Callback imzası: `async def handler(payload: dict) -> None`.
- Subscribe: `event_bus.subscribe("event.type", self.handler)`.
- Unsubscribe: bileşen kapanırken gerekiyorsa `event_bus.unsubscribe()`.
- Exception handler içinde yakalanmalı — bir subscriber'ın hatası diğerlerini etkilemez.
- Singleton event bus: `get_event_bus()` ile.

---

## Guidelines

Subscription pattern'ı:
```python
from src.core.event_bus import get_event_bus

class OrchestratorTelegramBot:
    def __init__(self):
        self._event_bus = get_event_bus()
    
    async def start(self):
        # Event'lere abone ol
        self._event_bus.subscribe("plan.approval_needed", self._on_approval_needed)
        self._event_bus.subscribe("sprint.completed", self._on_sprint_completed)
        self._event_bus.subscribe("worker.failed", self._on_worker_failed)
        self._event_bus.subscribe("error.occurred", self._on_error)
    
    async def _on_approval_needed(self, payload: dict) -> None:
        try:
            project_id = payload.get("project_id", "unknown")
            approval = payload.get("approval_request", {})
            
            message = f"✋ Onay gerekiyor: {approval.get('reason', '')}"
            await self._send_message(message)
        except Exception as e:
            logger.error(f"Telegram approval notification hatası: {e}")
    
    async def _on_sprint_completed(self, payload: dict) -> None:
        try:
            await self._send_message(
                f"✅ Sprint tamamlandı: {payload.get('project_id')}"
            )
        except Exception as e:
            logger.error(f"Telegram sprint notification hatası: {e}")
```

One-time subscriber (tek sefer dinle):
```python
future: asyncio.Future = asyncio.get_event_loop().create_future()

def one_time_handler(payload: dict):
    if not future.done():
        future.set_result(payload)
    event_bus.unsubscribe("plan.approved", one_time_handler)

event_bus.subscribe("plan.approved", one_time_handler)
result = await asyncio.wait_for(future, timeout=900)  # 15 dakika
```

---

## References

- `event-emission-pattern-skill/SKILL.md` — emit
- `telegram-bot-patterns-skill/SKILL.md` — Telegram entegrasyonu
- `event-driven-pattern-validation-skill/SKILL.md` — review
