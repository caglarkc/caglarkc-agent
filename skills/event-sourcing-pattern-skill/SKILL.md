---
name: event-sourcing-pattern
description: Coder AI için — sistem durumunu olaylar dizisi olarak saklamak; state'i olaylardan yeniden oluşturmak.
---

## Purpose

State direkt güncelleme yerine olaylar (events) kayıt altına alınır.
Herhangi bir andaki state: olaylar baştan tekrar oynatılarak elde edilir.
Debug, audit ve time-travel için güçlü temel sağlar.

---

## When to Apply

- Sprint state değişimlerinin tam geçmişi gerektiğinde
- "Nasıl bu duruma geldik?" sorusu izlenebilir olmalıyken
- Event replay veya partial recovery yapılırken

---

## Rules

- Her state değişikliği bir olay olarak emit edilir.
- Olaylar immutable — değiştirilmez, yalnızca eklenir.
- Olay yapısı: event_type, payload, timestamp, sequence_number.
- State rehydration: olaylar sırayla uygulanır.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DomainEvent:
    event_type: str
    payload:    dict
    timestamp:  str = field(default_factory=lambda: datetime.utcnow().isoformat())
    sequence:   int = 0

EVENT_HANDLERS: dict[str, callable] = {}

def register_handler(event_type: str):
    def decorator(fn):
        EVENT_HANDLERS[event_type] = fn
        return fn
    return decorator

@register_handler("task.status_changed")
def handle_task_status(state: dict, event: DomainEvent) -> dict:
    registry = dict(state.get("file_registry", {}))
    registry[event.payload["file_path"]] = event.payload["new_status"]
    return {**state, "file_registry": registry}

@register_handler("sprint.started")
def handle_sprint_started(state: dict, event: DomainEvent) -> dict:
    return {**state, "sprint_status": "running", "sprint_started_at": event.timestamp}

def rehydrate_state(events: list[DomainEvent], initial_state: dict | None = None) -> dict:
    state = initial_state or {}
    for event in sorted(events, key=lambda e: e.sequence):
        handler = EVENT_HANDLERS.get(event.event_type)
        if handler:
            state = handler(state, event)
    return state
```

---

## References

- `event-replay-skill/SKILL.md` — olay tekrar oynatma
- `checkpoint-inspection-skill/SKILL.md` — checkpoint inceleme
- `state-snapshot-diff-skill/SKILL.md` — state diff
