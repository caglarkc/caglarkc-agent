---
name: worker-idle-detection
description: Coder AI için — atanmış görevi olmayan boşta bekleyen worker'ları tespit edip yeni görev atamak veya kapatmak.
---

## Purpose

Boşta bekleyen worker kaynak tüketir (bellek, bağlantı).
Idle detection: kuyrukta iş yoksa worker bekleme moduna alınır.
Yeni iş geldiğinde: idle worker önce uyandırılır, yeni worker açılmaz.

---

## When to Apply

- Dispatcher yeni görev atamadan önce boşta worker var mı kontrol ederken
- Kaynak optimizasyonu gerektiğinde
- Sprint bittikten sonra worker'lar temizlenirken

---

## Rules

- Idle eşiği: 30 saniye görevsiz = idle.
- Idle worker: önce yeni göreve atanır.
- Sprint bittikten sonra: tüm idle worker'lar kapatılır.
- Worker kapat: `stop_event.set()` ile graceful shutdown.

---

## Guidelines

```python
import asyncio
from datetime import datetime, timedelta

IDLE_THRESHOLD_SECONDS = 30

class WorkerPool:
    def __init__(self):
        self._workers: dict[str, dict] = {}
    
    def register(self, worker_id: str) -> None:
        self._workers[worker_id] = {
            "status":   "idle",
            "idle_since": datetime.utcnow().isoformat(),
            "stop_event": asyncio.Event(),
        }
    
    def mark_busy(self, worker_id: str) -> None:
        if worker_id in self._workers:
            self._workers[worker_id]["status"]     = "busy"
            self._workers[worker_id]["idle_since"] = None
    
    def mark_idle(self, worker_id: str) -> None:
        if worker_id in self._workers:
            self._workers[worker_id]["status"]     = "idle"
            self._workers[worker_id]["idle_since"] = datetime.utcnow().isoformat()
    
    def get_idle_workers(self) -> list[str]:
        return [
            wid for wid, info in self._workers.items()
            if info["status"] == "idle"
        ]
    
    def get_long_idle_workers(self) -> list[str]:
        threshold = datetime.utcnow() - timedelta(seconds=IDLE_THRESHOLD_SECONDS)
        return [
            wid for wid, info in self._workers.items()
            if info["status"] == "idle" and info.get("idle_since")
            and datetime.fromisoformat(info["idle_since"]) < threshold
        ]
    
    async def stop_idle_workers(self) -> int:
        idle = self.get_long_idle_workers()
        for wid in idle:
            self._workers[wid]["stop_event"].set()
            del self._workers[wid]
        return len(idle)
    
    def get_first_idle(self) -> str | None:
        idle = self.get_idle_workers()
        return idle[0] if idle else None
```

---

## References

- `worker-heartbeat-skill/SKILL.md` — worker heartbeat
- `worker-status-tracking-skill/SKILL.md` — worker durum takibi
- `worker-concurrency-control-skill/SKILL.md` — eşzamanlılık kontrolü
