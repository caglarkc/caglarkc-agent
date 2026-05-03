---
name: worker-result-aggregation
description: Coder AI için — paralel worker'lardan gelen sonuçları toplayıp birleştirmek; eksik veya hatalı sonuçları işlemek.
---

## Purpose

3 worker paralel çalıştı — sonuçları tek state güncellemesine dönüştürmek gerekiyor.
Aggregation: başarılı sonuçları birleştirir, başarısızları ayrı listeler.
Kısmi başarı: bazı worker'lar başarısız olsa da sprint ilerler.

---

## When to Apply

- `asyncio.gather` ile paralel worker çağrısı sonrasında
- Dispatcher birden fazla worker sonucu beklediğinde
- Kısmi başarı kabul edilebilir iş akışında

---

## Rules

- Toplama: tüm worker'lar tamamlanana kadar bekle (gather).
- Hata: `return_exceptions=True` ile toplu yakalanır.
- Başarılı sonuçlar: `generated_files` dict'ine eklenir.
- Başarısız sonuçlar: `failed_tasks` listesine, retry kuyruğuna.

---

## Guidelines

```python
import asyncio

async def run_workers_parallel(
    worker_tasks: list[dict],
    graph,
    sprint_id: str,
) -> dict:
    coros = [
        run_single_worker(task, graph, sprint_id)
        for task in worker_tasks
    ]
    
    results = await asyncio.gather(*coros, return_exceptions=True)
    
    return aggregate_worker_results(worker_tasks, results)

async def run_single_worker(task: dict, graph, sprint_id: str) -> dict:
    config = {"configurable": {"thread_id": f"{sprint_id}_{task['id']}"}}
    result = await graph.ainvoke({"current_task": task}, config=config)
    return result

def aggregate_worker_results(
    tasks: list[dict],
    results: list,
) -> dict:
    generated_files = {}
    failed_tasks    = []
    completed_tasks = []
    
    for task, result in zip(tasks, results):
        if isinstance(result, Exception):
            failed_tasks.append({
                "task_id": task["id"],
                "error":   str(result),
            })
        else:
            files = result.get("generated_files", {})
            generated_files.update(files)
            completed_tasks.append(task["id"])
    
    return {
        "generated_files":  generated_files,
        "failed_tasks":     failed_tasks,
        "completed_tasks":  completed_tasks,
        "partial_success":  len(failed_tasks) > 0 and len(completed_tasks) > 0,
    }
```

---

## References

- `dispatcher-node-implementation-skill/SKILL.md` — dispatcher
- `worker-assignment-strategy-skill/SKILL.md` — worker atama
- `dead-letter-queue-skill/SKILL.md` — başarısız görev kuyruğu
