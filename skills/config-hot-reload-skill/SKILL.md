---
name: config-hot-reload
description: Coder AI için — daemon çalışırken .env dosyasındaki değişiklikleri yeniden başlatmadan yüklemek; dinamik konfigürasyon güncelleme.
---

## Purpose

Daemon yeniden başlatmak çalışan sprint'i bozabilir.
`.env` değiştiğinde ayarlar yeniden yüklenerek restart önlenir.
Özellikle API key rotasyonu veya log seviyesi değişikliği için.

---

## When to Apply

- API key değiştiğinde daemon'ın yeni key'i kullanması gerektiğinde
- Log seviyesi runtime'da değiştirilmek istendiğinde
- `.env` izleme özelliği eklenmesi gerektiğinde

---

## Rules

- Yeniden yükleme: `watchdog` veya periyodik kontrol ile.
- Kritik değişiklik (DB path): yeniden yükleme yapılmaz, uyarı verilir.
- API key değişikliği: yeni LLM instance oluşturulur.
- Hot reload: sadece opsiyonel ayarlar için güvenli.

---

## Guidelines

```python
import asyncio
from pathlib import Path

class ConfigWatcher:
    def __init__(
        self,
        env_path: str = ".env",
        check_interval: float = 30.0,
    ):
        self._env_path = Path(env_path)
        self._interval = check_interval
        self._last_mtime: float | None = None
        self._callbacks: list = []
    
    def on_change(self, callback) -> None:
        self._callbacks.append(callback)
    
    async def watch(self) -> None:
        while True:
            await asyncio.sleep(self._interval)
            try:
                mtime = self._env_path.stat().st_mtime
                if self._last_mtime and mtime != self._last_mtime:
                    logger.info(".env değişti, yeniden yükleniyor...")
                    await self._reload()
                self._last_mtime = mtime
            except OSError:
                pass
    
    async def _reload(self) -> None:
        try:
            new_settings = Settings()
            for callback in self._callbacks:
                await callback(new_settings)
            logger.info("Konfigürasyon yeniden yüklendi")
        except Exception as e:
            logger.error(f"Config yeniden yükleme hatası: {e}")

# Kullanım
watcher = ConfigWatcher()

async def on_config_change(new_settings: Settings) -> None:
    global current_llm
    # Yeni API key ile yeni LLM instance
    current_llm = create_planner_llm(new_settings)

watcher.on_change(on_config_change)
asyncio.create_task(watcher.watch())
```

---

## References

- `settings-validation-skill/SKILL.md` — settings
- `daemon-ops-skill/SKILL.md` — daemon yönetimi
- `graceful-shutdown-implementation-skill/SKILL.md` — shutdown
