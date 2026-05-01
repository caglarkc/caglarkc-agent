---
name: thread-config-management
description: Coder AI için — LangGraph thread ID'lerini proje başına yönetme, thread-config mapping ve birden fazla projenin aynı anda izolasyonu.
---

## Purpose

Her projenin kendi izole graph thread'inde çalışmasını sağlar.
Thread ID karışması iki projenin state'inin birbirine karışmasına yol açar.
Thread-project mapping tutarlı tutulur.

---

## When to Apply

- Yeni proje oluşturulduğunda
- Graph çağrısı yapılırken
- Pending thread'ler resume edilirken
- Multi-project ortamında izolasyon sağlanırken

---

## Rules

- Thread ID formatı: `f"{GRAPH_THREAD_PREFIX}_{project_id}"` — değiştirilmez.
- `GRAPH_THREAD_PREFIX` settings'ten okunur.
- Her proje sadece 1 aktif thread'e sahip olabilir.
- Thread ID → project_id mapping `GraphManager`'da tutulur.
- Thread ID hiçbir zaman UUID'siz oluşturulmaz (project_id zaten UUID).

---

## Guidelines

Thread ID yönetimi:
```python
from src.config.settings import get_settings

settings = get_settings()

def get_thread_id(project_id: str) -> str:
    return f"{settings.graph_thread_prefix}_{project_id}"

def get_thread_config(project_id: str) -> dict:
    return {"configurable": {"thread_id": get_thread_id(project_id)}}
```

GraphManager'da mapping:
```python
class GraphManager:
    def __init__(self):
        self._thread_map: dict[str, str] = {}  # project_id → thread_id
        self._lock = asyncio.Lock()
    
    async def register_project(self, project_id: str) -> str:
        thread_id = get_thread_id(project_id)
        async with self._lock:
            self._thread_map[project_id] = thread_id
        return thread_id
    
    async def get_active_projects(self) -> list[str]:
        async with self._lock:
            return list(self._thread_map.keys())
```

Recovery sırasında thread listeleme:
```python
async def recover_pending_threads(self, compiled_graph):
    for project_id, project_state in state_manager.get_all():
        if project_state.get("status") in ("running", "pending"):
            config = get_thread_config(project_id)
            current = await compiled_graph.aget_state(config=config)
            if current.next:
                logger.info(f"Resume: {project_id}, next: {current.next}")
                await compiled_graph.ainvoke(None, config=config)
```

---

## References

- `graph-invocation-async-skill/SKILL.md` — graph çalıştırma
- `graph-state-inspection-skill/SKILL.md` — state okuma
- `checkpoint-strategy-review-skill/SKILL.md` — checkpoint
