---
name: graph-hot-reload
description: Coder AI için — LangGraph iş akışını yeniden başlatmadan güncellemek; node değişikliklerini canlı uygulamak.
---

## Purpose

Her kod değişikliğinde tüm sistemi yeniden başlatmak geliştirmeyi yavaşlatır.
Hot reload: graph yeniden compile edilir, aktif checkpoint korunur.
Yalnızca geliştirme ortamında kullanılır — production'da klasik yeniden başlatma.

---

## When to Apply

- Geliştirme sırasında node mantığı değiştirildiğinde
- `watchdog` dosya değişikliği algıladığında
- Hızlı iterasyon döngüsü kurulurken

---

## Rules

- Sadece dev ortamı: `DEBUG=true` veya `ENV=development`.
- Checkpoint: reload sırasında kaydedilir, kaybolmaz.
- Aktif sprint: reload sonrası devam eder.
- Production'da: bu özellik devre dışı — klasik restart.

---

## Guidelines

```python
import importlib
import asyncio
from pathlib import Path

class GraphHotReloader:
    def __init__(self, graph_module_path: str, checkpointer):
        self._module_path  = graph_module_path
        self._checkpointer = checkpointer
        self._graph = None
        self._lock  = asyncio.Lock()
    
    async def load(self) -> None:
        async with self._lock:
            module = importlib.import_module(self._module_path)
            importlib.reload(module)
            build_fn = getattr(module, "build_graph")
            self._graph = await build_fn(self._checkpointer)
    
    async def reload(self) -> None:
        import logging
        logging.getLogger(__name__).info("Graph yeniden yükleniyor...")
        await self.load()
        logging.getLogger(__name__).info("Graph yeniden yüklendi.")
    
    @property
    def graph(self):
        return self._graph

# Dosya izleyici ile entegrasyon
async def watch_and_reload(reloader: GraphHotReloader, watch_dir: str) -> None:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class ReloadHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith(".py"):
                asyncio.create_task(reloader.reload())
    
    observer = Observer()
    observer.schedule(ReloadHandler(), watch_dir, recursive=True)
    observer.start()
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        observer.stop()
```

---

## References

- `config-hot-reload-skill/SKILL.md` — config hot reload
- `graph-assembly-skill/SKILL.md` — graf montajı
- `state-persistence-recovery-skill/SKILL.md` — state kalıcılığı
