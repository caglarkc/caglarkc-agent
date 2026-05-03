---
name: worker-status-tracking
description: Coder AI için — aktif worker'ların durumunu (idle/busy/failed) OrchestratorState içinde takip etmek; kapasite yönetimi için worker sayısını güncel tutmak.
---

## Purpose

Kaç worker aktif, kaçı boşta — dispatcher bu bilgiyle yeni iş atar.
Worker'ın çöktüğü bilinmezse atanan dosyalar askıda kalır.
Worker registry, dispatcher'ın kapasite kararlarını besler.

---

## When to Apply

- Executor node'da worker başlatılırken
- Worker tamamlandığında veya çöktüğünde
- Dispatcher kapasite kontrolü yaparken
- Recovery sırasında orphan worker tespitinde

---

## Rules

- `active_workers` dict: `{worker_id: WorkerInfo}` yapısında.
- Worker başlangıcında `status="busy"` ile eklenir.
- Worker bitişinde registry'den kaldırılır veya `status="idle"` yapılır.
- `max_concurrent_workers` aşılırsa yeni worker başlatılmaz.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class WorkerInfo:
    worker_id: str
    file_path: str
    status: str  # "busy" | "idle" | "failed"
    started_at: datetime = field(default_factory=datetime.utcnow)
    task_id: str | None = None

def register_worker(
    state: OrchestratorState,
    worker_id: str,
    file_path: str,
    task_id: str | None = None
) -> dict[str, dict]:
    workers = dict(state.get("active_workers", {}))
    workers[worker_id] = {
        "file_path": file_path,
        "status": "busy",
        "started_at": datetime.utcnow().isoformat(),
        "task_id": task_id,
    }
    return workers

def unregister_worker(
    state: OrchestratorState,
    worker_id: str
) -> dict[str, dict]:
    workers = dict(state.get("active_workers", {}))
    workers.pop(worker_id, None)
    return workers

def get_active_worker_count(state: OrchestratorState) -> int:
    return len(state.get("active_workers", {}))

def can_start_new_worker(
    state: OrchestratorState,
    max_workers: int = 3
) -> bool:
    return get_active_worker_count(state) < max_workers
```

State update pattern:
```python
# Executor node içinde
new_workers = register_worker(state, worker_id, file_path)
return {"active_workers": new_workers}
```

---

## References

- `file-status-state-machine-skill/SKILL.md` — dosya durumu
- `queue-entry-construction-skill/SKILL.md` — kuyruk yönetimi
- `partial-sprint-recovery-skill/SKILL.md` — recovery
