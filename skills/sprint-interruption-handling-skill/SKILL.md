---
name: sprint-interruption-handling
description: Planner AI için — kullanıcının sprint ortasında gönderdiği yeni isteği veya değişikliği işlemek; çalışan sprinti güvenli şekilde duraklatmak.
---

## Purpose

Sprint çalışırken kullanıcı "dur, şunu da ekle" diyebilir.
Interruption handling: mesaj sprint ortasında gelince duraklatma + işleme + devam.
Veri kaybı olmadan akış yönetimi.

---

## When to Apply

- Kullanıcı aktif sprint sırasında mesaj gönderdiğinde
- Sprint çalışırken yeni görev eklenmesi istendiğinde
- Kullanıcı "dur/değiştir/iptal et" dediğinde

---

## Rules

- Interrupt: aktif görev tamamlanana kadar bekle (max 30s).
- İşle: kullanıcı mesajını kategorize et (yeni görev, değişiklik, iptal).
- Devam: interrupt öncesi state'e ek değişiklikle devam.
- Çift interrupt: önce geleni işle, sonraki kuyruğa al.

---

## Guidelines

```python
import asyncio
from enum import Enum

class InterruptType(str, Enum):
    ADD_TASK   = "add_task"
    CANCEL     = "cancel"
    MODIFY     = "modify"
    STATUS     = "status"
    OTHER      = "other"

def classify_interrupt(message: str) -> InterruptType:
    msg = message.lower()
    if any(k in msg for k in ["iptal", "dur", "cancel", "stop"]):
        return InterruptType.CANCEL
    if any(k in msg for k in ["ekle", "add", "yeni", "new"]):
        return InterruptType.ADD_TASK
    if any(k in msg for k in ["değiştir", "modify", "güncelle", "update"]):
        return InterruptType.MODIFY
    if any(k in msg for k in ["durum", "status", "ne kadar", "ilerleme"]):
        return InterruptType.STATUS
    return InterruptType.OTHER

async def handle_sprint_interrupt(
    interrupt_msg: str,
    state: dict,
    pause_event: asyncio.Event,
    resume_event: asyncio.Event,
) -> dict:
    interrupt_type = classify_interrupt(interrupt_msg)

    # Sprint'i duraklat
    pause_event.set()
    await asyncio.sleep(0.1)  # Aktif görevin durmasını bekle

    updates = {}
    if interrupt_type == InterruptType.CANCEL:
        updates = {"sprint_status": "cancelled", "cancellation_reason": interrupt_msg}
    elif interrupt_type == InterruptType.STATUS:
        # Sadece durum raporu — sprint devam eder
        resume_event.set()
        return {"status_requested": True}
    elif interrupt_type == InterruptType.ADD_TASK:
        updates = {"pending_interrupt": {"type": "add", "message": interrupt_msg}}
        resume_event.set()
    else:
        resume_event.set()

    return updates
```

---

## References

- `sprint-pause-resume-skill/SKILL.md` — duraklama/devam
- `approval-flow-orchestration-skill/SKILL.md` — onay akışı
- `sprint-cancellation-skill/SKILL.md` — sprint iptal
