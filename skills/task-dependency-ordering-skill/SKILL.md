---
name: task-dependency-ordering
description: Planner AI için — sprint görevleri arasındaki bağımlılıkları belirleyerek doğru çalışma sırasını oluşturmak; bağımlı görevin öncekinden önce başlamasını önlemek.
---

## Purpose

`models.py` yazılmadan önce `repository.py` yazılırsa import hatası olur.
Görev bağımlılıkları topological sort ile sıralanır.
Döngüsel bağımlılık tespit edilirse planlama durdurulur.

---

## When to Apply

- Sprint planı oluşturulurken görev sırası belirlenirken
- Dispatcher görev kuyruğu hazırlanırken
- Bağımlı dosyalar `context_files` listesine eklenirken

---

## Rules

- Bağımlılık grafiği oluştur: hangi görev hangi göreve bağlı.
- Topological sort ile doğru sıra hesapla.
- Döngüsel bağımlılık varsa `CyclicDependencyError` fırlat.
- Bağımsız görevler paralel çalışabilir — sıraya birlikte eklenebilir.

---

## Guidelines

```python
from collections import defaultdict, deque
from typing import TypeVar

class CyclicDependencyError(Exception):
    pass

def topological_sort(
    tasks: list[dict],
    dependency_key: str = "depends_on"
) -> list[dict]:
    """Kahn algoritması ile topological sort."""
    task_map = {t["task_id"]: t for t in tasks}
    in_degree = defaultdict(int)
    graph = defaultdict(list)
    
    for task in tasks:
        for dep in task.get(dependency_key, []):
            graph[dep].append(task["task_id"])
            in_degree[task["task_id"]] += 1
    
    queue = deque(
        t["task_id"] for t in tasks
        if in_degree[t["task_id"]] == 0
    )
    result = []
    
    while queue:
        task_id = queue.popleft()
        result.append(task_map[task_id])
        for neighbor in graph[task_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(result) != len(tasks):
        raise CyclicDependencyError(
            "Görevler arasında döngüsel bağımlılık tespit edildi"
        )
    
    return result
```

PM'in görev sıralama kararı:
```
[PLANLAMA] Görev bağımlılıkları tespit edildi:

1. models.py → bağımlılık yok (önce)
2. repository.py → models.py'a bağımlı
3. service.py → repository.py'a bağımlı
4. api.py → service.py'a bağımlı

Sıra: models → repository → service → api
```

---

## References

- `sprint-task-decomposition-skill/SKILL.md` — görev ayrıştırma
- `queue-entry-construction-skill/SKILL.md` — kuyruk oluşturma
- `scope-boundary-detection-skill/SKILL.md` — kapsam
