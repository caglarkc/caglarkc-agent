---
name: sprint-progress-persistence
description: Coder AI için — sprint ilerleme verilerini düzenli aralıklarla DB'ye yazmak; uygulama yeniden başlasa da devam edilebilsin.
---

## Purpose

İşlem hafızada saklansa yeniden başlatmada kaybolur.
Progress persistence: her önemli adımda ilerleme DB'ye yazılır.
Çöküş sonrası: tamamlanan görevler tekrar yapılmaz.

---

## When to Apply

- Worker her dosyayı tamamladığında
- Sprint durumu değiştiğinde (running, paused, completed)
- Uygulama kapanmadan önce graceful shutdown sırasında

---

## Rules

- Kayıt: her `done` durumuna geçişte.
- Periyodik: 60 saniyede bir toplu kayıt.
- Yazma hatası: sprint durdurmaz, log + retry.
- Recovery: DB'den son state okunur, eksikler hesaplanır.

---

## Guidelines

```python
import asyncio
import json
from datetime import datetime

PERSIST_INTERVAL = 60.0

async def periodic_persistence_loop(
    state_getter,      # () -> dict
    db_writer,         # (dict) -> None
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        try:
            state = state_getter()
            await db_writer(serialize_progress(state))
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Progress persist hatası: %s", exc)
        
        try:
            await asyncio.wait_for(
                asyncio.shield(stop_event.wait()),
                timeout=PERSIST_INTERVAL,
            )
        except asyncio.TimeoutError:
            pass

def serialize_progress(state: dict) -> dict:
    return {
        "sprint_id":     state.get("sprint_id"),
        "sprint_status": state.get("sprint_status"),
        "file_registry": state.get("file_registry", {}),
        "completed_tasks": [
            t["id"] for t in state.get("tasks", [])
            if t.get("status") == "done"
        ],
        "saved_at": datetime.utcnow().isoformat(),
    }

async def restore_progress(db_reader, sprint_id: str) -> dict | None:
    raw = await db_reader(sprint_id)
    if not raw:
        return None
    return json.loads(raw) if isinstance(raw, str) else raw

def merge_restored_state(current: dict, restored: dict) -> dict:
    merged = dict(current)
    for task in merged.get("tasks", []):
        if task["id"] in restored.get("completed_tasks", []):
            task["status"] = "done"
    merged["file_registry"] = {
        **merged.get("file_registry", {}),
        **restored.get("file_registry", {}),
    }
    return merged
```

---

## References

- `state-persistence-recovery-skill/SKILL.md` — state kalıcılığı
- `checkpoint-inspection-skill/SKILL.md` — checkpoint inceleme
- `partial-sprint-recovery-skill/SKILL.md` — kısmi kurtarma
