---
name: sprint-parallel-execution
description: Planner AI için — bağımsız görevleri paralel worker'lara dağıtarak sprint süresini kısaltmak.
---

## Purpose

Sıralı yürütme kapasite israfıdır — birbirinden bağımsız görevler bekler.
Paralel yürütme: bağımlılığı olmayan görevler aynı anda çalışır.
3 worker ile 3× hızlanma mümkündür (teorik üst sınır).

---

## When to Apply

- Sprint planında bağımsız görevler varken
- `MAX_CONCURRENT_WORKERS > 1` konfigürasyonunda
- Dispatcher görevleri worker kuyruğuna doldururken

---

## Rules

- Paralel görev: `depends_on` alanı boş veya tüm bağımlılıklar `done`.
- Çalışan worker sayısı: `MAX_CONCURRENT_WORKERS` ile sınırlı.
- Dosya çakışması kontrolü: paralel atama öncesi yapılır.
- Timeout: en uzun süren paralel görev sprint süresini belirler.

---

## Guidelines

```python
import asyncio
from collections import defaultdict

def get_runnable_tasks(
    tasks: list[dict],
    completed_ids: set[str],
    max_parallel: int = 3,
) -> list[dict]:
    runnable = []
    for task in tasks:
        if task.get("status") != "planned":
            continue
        deps = set(task.get("depends_on", []))
        if deps.issubset(completed_ids):
            runnable.append(task)
        if len(runnable) >= max_parallel:
            break
    return runnable

async def run_parallel_batch(
    tasks: list[dict],
    execute_fn,
) -> list[dict]:
    results = await asyncio.gather(
        *[execute_fn(task) for task in tasks],
        return_exceptions=True,
    )
    updates = []
    for task, result in zip(tasks, results):
        if isinstance(result, Exception):
            updates.append({**task, "status": "failed", "last_error": str(result)})
        else:
            updates.append({**task, "status": "done", **result})
    return updates

async def execute_sprint_parallel(tasks: list[dict], execute_fn, max_parallel: int = 3) -> list[dict]:
    all_tasks  = list(tasks)
    completed  = set()
    task_map   = {t["id"]: t for t in all_tasks}

    while True:
        runnable = get_runnable_tasks(
            [t for t in all_tasks if t.get("status") == "planned"],
            completed, max_parallel,
        )
        if not runnable:
            break
        results = await run_parallel_batch(runnable, execute_fn)
        for r in results:
            task_map[r["id"]] = r
            if r["status"] == "done":
                completed.add(r["id"])

    return list(task_map.values())
```

---

## References

- `worker-assignment-strategy-skill/SKILL.md` — worker atama
- `dispatcher-node-implementation-skill/SKILL.md` — dispatcher
- `sprint-conflict-resolution-skill/SKILL.md` — çakışma çözümü
