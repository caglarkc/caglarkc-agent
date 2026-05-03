---
name: sprint-abort-on-critical-failure
description: Planner AI için — kritik hata oluştuğunda devam etmek yerine sprinti temiz şekilde durdurmak.
---

## Purpose

Kritik bileşen başarısız olunca devam etmek zamanı ve kaynakları boşa harcar.
Kritik hata tespiti: bağımlılıklar yerine getirilmeden devam edilemez.
Temiz abort: state güncellenir, kullanıcı bilgilendirilir, retry seçeneği sunulur.

---

## When to Apply

- Temel altyapı dosyası (config, state, DB) üretilemeyen sprintte
- Planner node hata verdiğinde (sprint hiç başlayamıyor)
- Birden fazla worker kritik hatayla başarısız olduğunda

---

## Rules

- Kritik hata: sprint devam edemez tanımı planner tarafından yapılır.
- Abort: tüm aktif worker'lar durdurulur, state `aborted` olur.
- Mesaj: kullanıcıya neden abort edildiği, ne yapılabileceği.
- Retry: kullanıcı isteğiyle aynı plan tekrar denenebilir.

---

## Guidelines

```python
from dataclasses import dataclass

CRITICAL_ERROR_PATTERNS = [
    "config.py",       # Temel config dosyası başarısız
    "state.py",        # State tanımı başarısız
    "database_init",   # DB başlatma başarısız
    "AUTHENTICATION",  # Auth kritik
]

def is_critical_failure(task: dict, error: str) -> bool:
    file_path = task.get("file_path", "")
    return any(
        pattern in file_path or pattern in error
        for pattern in CRITICAL_ERROR_PATTERNS
    )

def build_abort_update(reason: str, failed_task: dict) -> dict:
    return {
        "sprint_status":    "aborted",
        "abort_reason":     reason,
        "abort_task_id":    failed_task.get("id"),
        "abort_timestamp":  __import__("datetime").datetime.utcnow().isoformat(),
    }

def format_abort_message(reason: str, failed_task: dict) -> str:
    return (
        f"🚨 Sprint durduruldu!\n\n"
        f"Neden: {reason}\n"
        f"Görev: {failed_task.get('description', failed_task.get('id'))}\n\n"
        f"Seçenekler:\n"
        f"  1. Hatayı düzeltin ve '/sprint retry' ile tekrar deneyin\n"
        f"  2. Planı revize edin ve yeni sprint başlatın"
    )

async def abort_sprint(
    state: dict,
    reason: str,
    failed_task: dict,
    event_bus,
    stop_events: list,
) -> dict:
    # Worker'ları durdur
    for ev in stop_events:
        ev.set()
    
    update = build_abort_update(reason, failed_task)
    msg    = format_abort_message(reason, failed_task)
    
    await event_bus.publish("user.notification", {"message": msg})
    return update
```

---

## References

- `sprint-cancellation-skill/SKILL.md` — sprint iptal
- `cascading-failure-prevention-skill/SKILL.md` — hata yayılma
- `sprint-blocker-resolution-skill/SKILL.md` — blocker çözümü
