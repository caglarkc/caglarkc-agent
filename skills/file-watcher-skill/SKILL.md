---
name: file-watcher
description: Coder AI için — proje dosyalarındaki değişiklikleri watchdog veya asyncio ile izlemek; değişen dosyaları otomatik yeniden işlemek.
---

## Purpose

Geliştirici dosyayı düzenlediğinde sprint dışı değişiklik tespit edilebilir.
File watcher bu değişiklikleri yakalayıp event olarak yayar.
Auto-reload veya drift detection için kullanılır.

---

## When to Apply

- Proje dosyaları dışarıdan değiştirildiğinde sistem haberdar edilmesi gerektiğinde
- "Dosya değişince otomatik test çalıştır" özelliği eklenirken
- Config dosyası izlenmesi gerektiğinde

---

## Rules

- `watchdog` kütüphanesi: cross-platform, güvenilir.
- Alternatif: asyncio ile periyodik `stat()` kontrolü.
- Yalnızca izlenen dizin ve uzantılar için olay üretilir.
- Çok hızlı değişiklikler debounce edilir (100ms).

---

## Guidelines

```python
import asyncio
from pathlib import Path

class SimpleFileWatcher:
    """asyncio tabanlı basit dosya izleyici."""
    
    def __init__(
        self,
        watch_paths: list[str],
        extensions: set[str] = {".py", ".toml", ".env"},
        poll_interval: float = 2.0,
    ):
        self._paths = [Path(p) for p in watch_paths]
        self._extensions = extensions
        self._interval = poll_interval
        self._mtimes: dict[str, float] = {}
        self._handlers: list = []
    
    def on_change(self, handler) -> None:
        self._handlers.append(handler)
    
    async def watch(self) -> None:
        # İlk snapshot
        self._mtimes = self._snapshot()
        
        while True:
            await asyncio.sleep(self._interval)
            current = self._snapshot()
            changed = self._find_changes(self._mtimes, current)
            
            if changed:
                for path in changed:
                    for h in self._handlers:
                        await h(path)
            
            self._mtimes = current
    
    def _snapshot(self) -> dict[str, float]:
        mtimes = {}
        for base in self._paths:
            for path in Path(base).rglob("*"):
                if path.suffix in self._extensions and path.is_file():
                    try:
                        mtimes[str(path)] = path.stat().st_mtime
                    except OSError:
                        pass
        return mtimes
    
    def _find_changes(
        self, before: dict, after: dict
    ) -> list[str]:
        changed = []
        for path, mtime in after.items():
            if before.get(path) != mtime:
                changed.append(path)
        return changed

# Kullanım
watcher = SimpleFileWatcher(watch_paths=["src/"])

async def on_file_change(path: str) -> None:
    logger.info(f"Dosya değişti: {path}")
    await event_bus.emit("file.changed", {"path": path})

watcher.on_change(on_file_change)
asyncio.create_task(watcher.watch())
```

---

## References

- `config-hot-reload-skill/SKILL.md` — config izleme
- `event-emission-pattern-skill/SKILL.md` — event emit
- `daemon-ops-skill/SKILL.md` — daemon yönetimi
