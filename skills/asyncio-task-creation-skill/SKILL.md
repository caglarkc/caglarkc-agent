---
name: asyncio-task-creation
description: Coder AI için — asyncio.create_task() ile background task oluşturmanın doğru yolu; task referansı yönetimi, iptal ve temizleme.
---

## Purpose

Background task'ların doğru oluşturulmasını ve yönetilmesini sağlar.
Referansız task'lar garbage collect edilip sessizce kaybolabilir.
Graceful shutdown için task'ların takip edilmesi zorunludur.

---

## When to Apply

- Daemon arka planda çalışan işler başlatırken
- Event listener veya heartbeat gibi sürekli çalışan coroutine başlatırken
- Paralel olmayan ama bloklamak istemediğin iş arka plana alınırken

---

## Rules

- `asyncio.create_task()` sonucu bir değişkene atanmalı (garbage collect koruması).
- Task set'te tutulur, done callback ile otomatik temizlenir.
- Uygulama kapanırken tüm task'lar iptal edilmeli ve `await` edilmeli.
- `task.cancel()` sonrası `CancelledError` yakalanmalı.
- `asyncio.ensure_future()` yerine `asyncio.create_task()` tercih edilir.

---

## Guidelines

Doğru task yönetimi:
```python
class OrchestratorDaemon:
    def __init__(self):
        self._background_tasks: set[asyncio.Task] = set()
    
    def _create_task(self, coro: Coroutine, name: str | None = None) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task
    
    async def start(self):
        # Heartbeat görevi
        self._create_task(self._heartbeat_loop(), name="heartbeat")
        # Stall detection
        self._create_task(self._stall_monitor(), name="stall-monitor")
    
    async def shutdown(self):
        for task in list(self._background_tasks):
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(
                *self._background_tasks,
                return_exceptions=True  # CancelledError'ı yakala
            )
        logger.info("Tüm background task'lar durduruldu")
```

Heartbeat döngüsü örneği:
```python
async def _heartbeat_loop(self):
    while True:
        try:
            await event_bus.emit("system.heartbeat", {
                "timestamp": datetime.utcnow().isoformat()
            })
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.debug("Heartbeat loop iptal edildi")
            raise  # CancelledError yeniden fırlatılmalı
        except Exception as e:
            logger.error(f"Heartbeat hatası: {e}")
            await asyncio.sleep(5)  # kısa bekleme, tekrar dene
```

---

## References

- `graceful-shutdown-implementation-skill/SKILL.md` — shutdown
- `asyncio-gather-usage-skill/SKILL.md` — parallel tasks
- `resource-cleanup-review-skill/SKILL.md` — kaynak temizliği
