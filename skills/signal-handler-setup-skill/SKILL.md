---
name: signal-handler-setup
description: Coder AI için — SIGTERM ve SIGINT sinyallerini yakalayarak daemon'ı temiz kapatan signal handler'ları kurmak.
---

## Purpose

`kill PID` veya Ctrl+C daemon'ı aniden öldürürse kayıt açık kalır, state bozulur.
Signal handler, kapanış sinyalini alır ve `graceful_shutdown()` tetikler.
Checkpoint'e son durum yazılır, DB bağlantısı kapatılır.

---

## When to Apply

- `src/daemon.py` veya `main.py` başlangıç kodu yazılırken
- Graceful shutdown mekanizması eklenmesi gerektiğinde
- `asyncio.run()` kullanılan entry point'te

---

## Rules

- `SIGTERM`: sistem kapatma — temiz kapanış.
- `SIGINT`: Ctrl+C — temiz kapanış.
- `SIGKILL`: yakalanamaz — bu için checkpoint var.
- Signal handler: `asyncio.get_event_loop().add_signal_handler()` ile.
- Shutdown: flag set et → event loop'u düzgünce bitir.

---

## Guidelines

```python
import asyncio
import signal

shutdown_event = asyncio.Event()

def setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    def handle_shutdown(sig: signal.Signals) -> None:
        logger.info(f"Sinyal alındı: {sig.name}, kapatılıyor...")
        shutdown_event.set()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda s=sig: handle_shutdown(s)
        )

async def main() -> None:
    loop = asyncio.get_event_loop()
    setup_signal_handlers(loop)
    
    # Uygulama başlat
    app = await start_application()
    
    # Kapanış sinyali bekle
    await shutdown_event.wait()
    
    # Temiz kapanış
    logger.info("Temiz kapanış başlıyor...")
    await app.shutdown()
    logger.info("Kapatıldı.")

if __name__ == "__main__":
    asyncio.run(main())
```

Graceful shutdown tamamlanma:
```python
async def shutdown(self) -> None:
    # Aktif worker'ların bitmesini bekle (max 30s)
    try:
        await asyncio.wait_for(
            self._wait_for_workers(),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        logger.warning("Worker timeout — zorla kapatılıyor")
    
    await self._close_connections()
```

---

## References

- `graceful-shutdown-implementation-skill/SKILL.md` — shutdown
- `daemon-ops-skill/SKILL.md` — daemon yönetimi
- `async-context-manager-skill/SKILL.md` — kaynak yönetimi
