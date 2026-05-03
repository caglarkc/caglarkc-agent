---
name: graceful-shutdown-implementation
description: Coder AI için — daemon'ın SIGTERM/SIGINT sinyallerini yakalayarak tüm aktif işlemleri temizce durdurmak, state'i flushe etmek ve bağlantıları kapatmak.
---

## Purpose

Daemon'ın beklenmedik kapanışta state kaybetmesini önler.
Açık DB bağlantılarını, background task'ları ve LangGraph thread'lerini temiz kapatır.
PID dosyasını temizleyerek bir sonraki başlatmada hatalı "zaten çalışıyor" mesajını önler.

---

## When to Apply

- `main.py` OrchestratorDaemon shutdown metodu yazılırken
- Yeni servis bileşeni (bot, CLI) shutdown hook'u gerektiğinde
- SIGTERM handler implementasyonu yapılırken

---

## Rules

- SIGTERM ve SIGINT sinyalleri yakalanmalı.
- Shutdown sırası: Interface → Graph → State flush → PID temizle.
- Background task'lar `task.cancel()` + `await gather(return_exceptions=True)`.
- State snapshot `flush_to_disk()` ile kaydedilmeli.
- PID dosyası silinmeli.
- Timeout: maksimum 30 saniye graceful shutdown, sonra force exit.

---

## Guidelines

Shutdown implementasyonu:
```python
import asyncio
import signal
from pathlib import Path

class OrchestratorDaemon:
    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._background_tasks: set[asyncio.Task] = set()
    
    async def start(self):
        # Signal handler kayıt
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(
                    self.shutdown(f"Signal {s.name}")
                )
            )
        
        # PID dosyası yaz
        settings.daemon_pid_path.write_text(str(os.getpid()))
        
        # Servisler başlat...
        
        # Shutdown bekle
        await self._shutdown_event.wait()
    
    async def shutdown(self, reason: str = "unknown"):
        logger.info(f"Shutdown başladı: {reason}")
        
        # 1. Interface'leri durdur
        if self._telegram_bot:
            await self._telegram_bot.stop()
        if self._cli:
            await self._cli.stop()
        
        # 2. Background task'ları iptal et
        for task in list(self._background_tasks):
            task.cancel()
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # 3. State'i diske yaz
        await state_manager.flush_to_disk()
        
        # 4. PID dosyasını temizle
        pid_path = settings.daemon_pid_path
        if pid_path.exists():
            pid_path.unlink()
        
        logger.info("Shutdown tamamlandı")
        self._shutdown_event.set()
```

---

## References

- `asyncio-task-creation-skill/SKILL.md` — task yönetimi
- `resource-cleanup-review-skill/SKILL.md` — kaynak temizliği
- `checkpoint-strategy-review-skill/SKILL.md` — state kalıcılığı
