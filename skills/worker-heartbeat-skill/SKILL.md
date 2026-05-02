---
name: worker-heartbeat
description: Coder AI için — aktif worker'ların canlılığını izlemek; yanıt vermeyen worker'ları tespit edip sistemi uyarmak.
---

## Purpose

Worker başlatılıp sonra sessizleşebilir — tamamlandı mı, takıldı mı bilinmez.
Heartbeat mekanizması düzenli aralıklarla worker'ın hâlâ çalıştığını kaydeder.
Timeout geçen worker dead olarak işaretlenir.

---

## When to Apply

- Worker node uzun süren görevler yürütürken
- Dispatcher worker durumunu kontrol etmek istediğinde
- Stall detection devreye girmeden önce erken uyarı gerektiğinde

---

## Rules

- Heartbeat aralığı: 10 saniye.
- Timeout: 3 kaçırılan heartbeat = dead (30s).
- Worker heartbeat'i state veya EventBus üzerinden günceller.
- Dead worker: görevi başka worker'a devret veya kullanıcıya bildir.

---

## Guidelines

```python
import asyncio
from datetime import datetime, timedelta

HEARTBEAT_INTERVAL = 10.0
HEARTBEAT_TIMEOUT  = 30.0

async def worker_heartbeat_loop(
    worker_id: str,
    event_bus,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        await event_bus.publish("worker.heartbeat", {
            "worker_id": worker_id,
            "ts": datetime.utcnow().isoformat(),
        })
        try:
            await asyncio.wait_for(
                asyncio.shield(stop_event.wait()),
                timeout=HEARTBEAT_INTERVAL,
            )
        except asyncio.TimeoutError:
            pass

def is_worker_alive(
    last_heartbeat: str | None,
    timeout: float = HEARTBEAT_TIMEOUT,
) -> bool:
    if not last_heartbeat:
        return False
    last = datetime.fromisoformat(last_heartbeat)
    return (datetime.utcnow() - last).total_seconds() < timeout

async def monitor_workers(
    state: dict,
    event_bus,
) -> list[str]:
    dead = []
    for wid, info in state.get("worker_registry", {}).items():
        if not is_worker_alive(info.get("last_heartbeat")):
            dead.append(wid)
            await event_bus.publish("worker.dead", {"worker_id": wid})
    return dead
```

---

## References

- `stall-detection-response-skill/SKILL.md` — genel takılma tespiti
- `worker-status-tracking-skill/SKILL.md` — worker durum kaydı
- `dead-letter-queue-skill/SKILL.md` — dead worker görev kurtarma
