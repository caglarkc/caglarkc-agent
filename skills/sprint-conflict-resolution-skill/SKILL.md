---
name: sprint-conflict-resolution
description: Planner AI için — aynı dosyayı düzenleyen iki görevi tespit edip çakışmayı çözmek; paralel yazım çakışmalarını önlemek.
---

## Purpose

İki worker aynı dosyayı aynı anda yazarsa sonuncu kazanır, diğeri kaybolur.
Conflict tespiti, paralel görevlerin aynı hedefe çakışmasını önler.
Çözüm: sıralama (biri önce biter, diğeri başlar) veya birleştirme.

---

## When to Apply

- Dispatcher görevleri worker'lara atamadan önce
- Aynı dosya birden fazla görevde geçtiğinde
- Sprint planı oluşturulurken çakışma analizi yapılırken

---

## Rules

- Çakışma: iki görev aynı `file_path` içeriyorsa.
- Çözüm stratejileri: serialize (sıraya koy), merge (birleştir), split (farklı dosyalara böl).
- Varsayılan: serialize — bağımlılık zinciri oluştur.
- Çakışma kaydı: sprint state'e eklenir.

---

## Guidelines

```python
from collections import defaultdict

def detect_file_conflicts(tasks: list[dict]) -> dict[str, list[str]]:
    """Aynı dosyayı hedefleyen görevleri döndür."""
    file_to_tasks: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        for f in task.get("files", []):
            file_to_tasks[f].append(task["id"])
    return {f: ids for f, ids in file_to_tasks.items() if len(ids) > 1}

def resolve_conflicts_by_serialization(
    tasks: list[dict],
    conflicts: dict[str, list[str]],
) -> list[dict]:
    resolved = list(tasks)
    task_map = {t["id"]: t for t in resolved}
    
    for file_path, task_ids in conflicts.items():
        # İlk göreve bağımlılık ekle
        for i in range(1, len(task_ids)):
            prev_id = task_ids[i - 1]
            curr_id = task_ids[i]
            task = task_map.get(curr_id)
            if task:
                deps = list(task.get("depends_on", []))
                if prev_id not in deps:
                    deps.append(prev_id)
                task["depends_on"] = deps
    
    return resolved

def log_conflict_resolution(
    conflicts: dict[str, list[str]],
    strategy: str = "serialize",
) -> list[dict]:
    return [
        {
            "file": f,
            "conflicting_tasks": ids,
            "resolution": strategy,
        }
        for f, ids in conflicts.items()
    ]
```

---

## References

- `task-dependency-ordering-skill/SKILL.md` — görev sıralama
- `worker-assignment-strategy-skill/SKILL.md` — worker atama
- `file-status-state-machine-skill/SKILL.md` — dosya durum makinesi
