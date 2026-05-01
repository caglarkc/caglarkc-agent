---
name: event-driven-pattern-validation
description: Planner AI için — event emit ve subscribe pattern'larının doğru uygulandığını, event isimlerinin tutarlı olduğunu ve event'lerin doğru payload ile gönderildiğini review sırasında kontrol etmek.
---

## Purpose

Event bus üzerinden iletişimin doğru kurulduğunu garantiler.
Emit edilen event'in subscriber tarafından beklenen formatla uyumluluğunu kontrol eder.
Event isim tutarsızlıklarını (typo, farklı namespace) yakalar.

---

## When to Apply

- EventBus `emit()` veya `subscribe()` çağrısı içeren kod review edilirken
- Yeni event tipi tanımlanırken
- Node'lar arası iletişim planlanırken

---

## Rules

- Event isimleri `namespace.action` formatında: `plan.generated`, `worker.failed`.
- Emit eden ve subscribe eden aynı event ismini kullanmalı (exact match).
- Payload zorunlu alanları her emit'te gönderilmeli.
- Subscriber callback imzası `async def handler(payload: dict)` olmalı.
- Event history 500 limit — yüksek frekanslı event'ler dikkatli planlanmalı.
- Error event'leri: `error.occurred` namespace kullanılır.

---

## Guidelines

Event isim standardı:
```
plan.approval_needed   — onay bekleniyor
plan.approved          — kullanıcı onayladı
plan.rejected          — kullanıcı reddetti
plan.generated         — taslak plan oluştu
task.received          — yeni görev alındı
manager.reply          — manager yanıt üretiyor
system.heartbeat       — worker atama bilgisi
system.stalled         — inaktivite tespit
system.recovered       — thread resume edildi
worker.failed          — worker tükendi
sprint.worker_done     — worker görevi tamamladı
sprint.completed       — sprint bitti
error.occurred         — exception yakalandı
```

Emit doğrulama:
```python
# DOĞRU
await event_bus.emit("plan.generated", {
    "project_id": state["project_id"],
    "draft_plan": state["draft_plan"],
    "timestamp": datetime.utcnow().isoformat()
})

# YANLIŞ
await event_bus.emit("planGenerated", {...})  # camelCase yasak
await event_bus.emit("plan_generated", {...})  # underscore değil nokta
```

Subscribe kontrol:
```python
# DOĞRU
event_bus.subscribe("plan.generated", self.on_plan_generated)

async def on_plan_generated(self, payload: dict):
    plan = payload.get("draft_plan")  # .get() ile güvenli erişim
```

---

## References

- `event-emission-pattern-skill/SKILL.md` — emit pattern'ları
- `event-subscription-pattern-skill/SKILL.md` — subscribe pattern'ları
- `cross-component-event-flow-skill/SKILL.md` — bileşenler arası akış
