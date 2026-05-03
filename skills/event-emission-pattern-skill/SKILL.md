---
name: event-emission-pattern
description: Coder AI için — EventBus üzerinden event emit etmenin standart yolu; EventEnvelope oluşturma, event isimlendirme ve payload yapısı.
---

## Purpose

Event emit'i standartlaştırır.
Her event doğru namespace, payload ve timestamp ile gönderilir.
Event bus singleton'a doğru erişim sağlanır.

---

## When to Apply

- LangGraph node'larında event emit edilirken
- Core servislerden durum bildirimi yapılırken
- Yeni event tipi ekleneceğinde

---

## Rules

- Event adı: `namespace.action` (nokta ile ayrılmış, lowercase).
- Event bus singleton: `get_event_bus()` ile erişilir.
- `await event_bus.emit(event_type, payload)` formatı.
- Payload: serializable dict, Pydantic model değil.
- Timestamp otomatik eklenmeli (EventBus eklemiyorsa manuel ekle).
- Exception emit edilmeden önce log'lanmalı.

---

## Guidelines

Event emit pattern'ı:
```python
from src.core.event_bus import get_event_bus
from datetime import datetime

event_bus = get_event_bus()

# Temel emit
await event_bus.emit("plan.generated", {
    "project_id": state.get("project_id"),
    "sprint_id": sprint_id,
    "files": list(file_registry.keys()),
    "timestamp": datetime.utcnow().isoformat()
})

# Hata event'i
await event_bus.emit("error.occurred", {
    "node": "planner",
    "project_id": project_id,
    "error": str(exception),
    "error_type": type(exception).__name__,
    "timestamp": datetime.utcnow().isoformat()
})

# Heartbeat
await event_bus.emit("system.heartbeat", {
    "project_id": project_id,
    "worker_id": worker_id,
    "task": target_file,
    "timestamp": datetime.utcnow().isoformat()
})
```

Event isimlendirme standardı:
```
plan.approval_needed  — onay isteniyor
plan.approved         — onay verildi
plan.rejected         — red verildi
plan.generated        — taslak hazır
task.received         — yeni görev
manager.reply         — manager yanıtı
worker.failed         — worker başarısız
sprint.worker_done    — worker tamamladı
sprint.completed      — sprint bitti
system.heartbeat      — canlılık sinyali
system.stalled        — inaktivite
system.recovered      — resume edildi
error.occurred        — hata oluştu
```

---

## References

- `event-subscription-pattern-skill/SKILL.md` — subscribe
- `event-driven-pattern-validation-skill/SKILL.md` — review
- `cross-component-event-flow-skill/SKILL.md` — akış
