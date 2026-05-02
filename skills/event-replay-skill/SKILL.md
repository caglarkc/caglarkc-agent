---
name: event-replay
description: Coder AI için — kaydedilen event'leri sırayla yeniden oynatarak sistemi belirli bir duruma getirmek; test ve debug için event sourcing benzeri pattern.
---

## Purpose

"Sprint nasıl bu duruma geldi?" sorusu event replay ile yanıtlanır.
Kayıtlı event'leri sırayla işleyerek state yeniden oluşturulur.
Test'te belirli senaryoları event sırasıyla tekrar oluşturmak kolaylaşır.

---

## When to Apply

- Hata ayıklama sırasında sprint'in hangi adımda bozulduğu araştırılırken
- Integration test'te belirli event sırası simüle edilirken
- Event log'undan durum yeniden oluşturulurken

---

## Rules

- Event'ler timestamp sırasıyla oynatılır.
- Her event işlendikten sonra state loglanır.
- Replay sadece read-only analiz için — gerçek side effect üretmez.
- Sandbox mod: gerçek DB ve LLM çağrısı yapılmaz.

---

## Guidelines

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RecordedEvent:
    event_id: str
    topic: str
    payload: dict
    timestamp: datetime

async def replay_events(
    events: list[RecordedEvent],
    initial_state: dict,
    event_handlers: dict[str, callable],
    sandbox: bool = True,
) -> list[dict]:
    """Event'leri sırayla oynatır, her adımın state'ini döndürür."""
    state = dict(initial_state)
    snapshots = [{"event": None, "state": dict(state)}]
    
    for event in sorted(events, key=lambda e: e.timestamp):
        handler = event_handlers.get(event.topic)
        
        if handler is None:
            logger.debug(f"Handler yok, atlandı: {event.topic}")
            continue
        
        if sandbox:
            # Sandbox: gerçek çağrı yapmadan state güncelle
            state_update = simulate_handler(event.topic, event.payload, state)
        else:
            state_update = await handler(event.payload, state)
        
        state.update(state_update)
        snapshots.append({
            "event": {"topic": event.topic, "ts": event.timestamp.isoformat()},
            "state": dict(state),
        })
    
    return snapshots

def simulate_handler(topic: str, payload: dict, state: dict) -> dict:
    """Sandbox: gerçek işlem yapmadan state simülasyonu."""
    if topic == "user.approval":
        return {"approval_status": "approved" if payload.get("approved") else "rejected"}
    elif topic == "worker.completed":
        registry = dict(state.get("file_registry", {}))
        registry[payload["file_path"]] = "done"
        return {"file_registry": registry}
    return {}
```

---

## References

- `message-bus-design-skill/SKILL.md` — event bus
- `graph-state-inspection-skill/SKILL.md` — state inceleme
- `integration-test-setup-skill/SKILL.md` — integration test
