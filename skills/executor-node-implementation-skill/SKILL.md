---
name: executor-node-implementation
description: Coder AI için — LangGraph executor node'unu implemente etmek; dispatch_queue'daki girişleri paralel worker task'larına dönüştürmek.
---

## Purpose

Executor, dispatcher'ın kuyruğa koyduğu işleri gerçekten başlatan node'dur.
`asyncio.gather` ile paralel worker çalışmasını koordine eder.
Worker sonuçlarını toplayıp state'e yazar.

---

## When to Apply

- `src/graph/nodes/executor.py` yazılırken
- Paralel kod üretimi koordinasyonu implemente edilirken
- Worker spawn ve cleanup mantığı eklenirken

---

## Rules

- `asyncio.gather(*tasks, return_exceptions=True)` ile paralel çalışma.
- `return_exceptions=True`: bir worker çöktüğünde diğerleri devam eder.
- Her worker sonucu kontrol edilir — exception varsa `failed` kaydedilir.
- Executor, worker sayısını `active_workers`'a ekler ve kaldırır.

---

## Guidelines

```python
# src/graph/nodes/executor.py
async def executor_node(state: OrchestratorState) -> OrchestratorState:
    queue_entries = state.get("dispatch_queue", [])
    
    if not queue_entries:
        return {}
    
    # Paralel worker task'ları oluştur
    worker_tasks = [
        _run_single_worker(entry, state)
        for entry in queue_entries
    ]
    
    results = await asyncio.gather(*worker_tasks, return_exceptions=True)
    
    # Sonuçları birleştir
    updated_registry = dict(state.get("file_registry", {}))
    
    for entry, result in zip(queue_entries, results):
        if isinstance(result, Exception):
            logger.error(f"Worker exception: {entry.file_path}: {result}")
            updated_registry[entry.file_path] = "failed"
        elif isinstance(result, dict):
            updated_registry.update(result.get("file_registry", {}))
    
    return {
        "file_registry": updated_registry,
        "dispatch_queue": [],   # kuyruk temizlendi
    }

async def _run_single_worker(
    entry: QueueEntry,
    state: OrchestratorState
) -> dict:
    worker_id = f"worker-{entry.entry_id[:8]}"
    logger.info(f"Worker başladı: {worker_id} → {entry.file_path}")
    
    result = await worker_node(state, entry)
    
    logger.info(f"Worker bitti: {worker_id}")
    return result
```

Graph akışı:
```
dispatcher → executor → validator → reviewer
```

---

## References

- `dispatcher-node-implementation-skill/SKILL.md` — dispatcher
- `worker-node-implementation-skill/SKILL.md` — worker
- `asyncio-gather-usage-skill/SKILL.md` — paralel çalışma
