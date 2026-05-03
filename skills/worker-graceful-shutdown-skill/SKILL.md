---
name: worker-graceful-shutdown
description: Coder AI için — worker'ları aniden kesmek yerine mevcut görevi bitirip temiz kapanmalarını sağlamak.
---

## Purpose

`kill -9` ile worker kesilirse yarım dosya, bozuk state kalır.
Graceful shutdown: stop sinyali gelince mevcut görev tamamlanır, sonra çıkılır.
State kaydedilir, checkpoint güncellenir, kaynak temizlenir.

---

## When to Apply

- Uygulama kapanmadan önce
- Sprint iptal edilirken aktif worker'lar varsa
- Kubernetes pod terminate sinyali aldığında

---

## Rules

- Sinyal: `SIGTERM` yakalanır, `stop_event` set edilir.
- Aktif görev: tamamlanana kadar beklenir (maks 30s).
- 30s sonrası: görev `interrupted` olarak işaretlenir.
- Checkpoint: kapatma öncesi son kez yazılır.

---

## Guidelines

```python
import asyncio
import signal

async def run_worker_with_graceful_shutdown(
    worker_fn,
    task_queue: asyncio.Queue,
    checkpoint_fn,
) -> None:
    stop_event = asyncio.Event()

    def handle_sigterm(*_):
        stop_event.set()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
    loop.add_signal_handler(signal.SIGINT,  handle_sigterm)

    current_task = None
    try:
        while not stop_event.is_set():
            try:
                task = await asyncio.wait_for(task_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            current_task = task
            try:
                await asyncio.wait_for(worker_fn(task), timeout=30.0)
                task_queue.task_done()
            except asyncio.TimeoutError:
                task["status"] = "interrupted"
            finally:
                current_task = None

    finally:
        if current_task:
            current_task["status"] = "interrupted"
        await checkpoint_fn()

async def shutdown_all_workers(
    stop_events: list[asyncio.Event],
    timeout: float = 35.0,
) -> None:
    for ev in stop_events:
        ev.set()
    await asyncio.sleep(timeout)
```

---

## References

- `signal-handler-setup-skill/SKILL.md` — sinyal işleyici
- `worker-heartbeat-skill/SKILL.md` — worker heartbeat
- `state-persistence-recovery-skill/SKILL.md` — state kalıcılığı
