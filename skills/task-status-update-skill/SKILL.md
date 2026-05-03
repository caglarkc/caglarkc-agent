---
name: task-status-update
description: Coder AI için — görev durumunu (pending/in_progress/done/failed) OrchestratorState içinde güncellemek; görev bazlı ilerleme takibi yapmak.
---

## Purpose

Dosya registry'si file düzeyinde takip yapar; task registry görev düzeyinde.
Hangi görevin tamamlandığı bilinmeden dispatcher doğru iş atayamaz.
Task durumu, sprint progress raporu için kaynak.

---

## When to Apply

- Worker dosya yazımını tamamladığında görev güncellenmesi gerektiğinde
- Dispatcher görev başlatırken
- Sprint tamamlanma kontrolünde

---

## Rules

- Task listesi `tasks` field'ında `list[dict]` olarak tutulur.
- Her task dict: `task_id`, `status`, `description`, `files`, `depends_on`.
- Status: `"pending"` → `"in_progress"` → `"done" | "failed"`.
- Task tüm dosyaları tamamlandığında `"done"` olur.
- State update: tüm tasks listesi güncellenerek yazılır (immutable pattern).

---

## Guidelines

```python
def update_task_status(
    tasks: list[dict],
    task_id: str,
    new_status: str,
) -> list[dict]:
    """İmmutable güncelleme — yeni liste döndürür."""
    updated = []
    for task in tasks:
        if task["task_id"] == task_id:
            updated.append({**task, "status": new_status})
        else:
            updated.append(task)
    return updated

def get_task_for_file(
    tasks: list[dict],
    file_path: str,
) -> dict | None:
    """Dosyaya ait görevi bulur."""
    for task in tasks:
        if file_path in task.get("files", []):
            return task
    return None

def is_task_complete(
    task: dict,
    file_registry: dict[str, str],
) -> bool:
    """Görevin tüm dosyaları done mı?"""
    files = task.get("files", [])
    if not files:
        return False
    return all(
        file_registry.get(f) == "done"
        for f in files
    )

def compute_task_statuses(
    tasks: list[dict],
    file_registry: dict[str, str],
) -> list[dict]:
    """file_registry'den task status'larını hesapla."""
    updated = []
    for task in tasks:
        if is_task_complete(task, file_registry):
            updated.append({**task, "status": "done"})
        else:
            updated.append(task)
    return updated
```

---

## References

- `file-status-state-machine-skill/SKILL.md` — dosya durumu
- `dispatcher-node-implementation-skill/SKILL.md` — dispatcher
- `progress-report-generation-skill/SKILL.md` — ilerleme raporu
