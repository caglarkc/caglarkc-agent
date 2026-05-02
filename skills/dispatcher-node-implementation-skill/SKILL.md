---
name: dispatcher-node-implementation
description: Coder AI için — LangGraph dispatcher node'unu implemente etmek; planned dosyaları reserved yapıp worker kuyruğuna atmak.
---

## Purpose

Dispatcher, planner'ın hazırladığı görev listesini worker'lara dağıtır.
Hangi dosyaların hangi sırayla işleneceğini belirler.
`MAX_CONCURRENT_WORKERS` kadar paralel iş başlatır.

---

## When to Apply

- `src/graph/nodes/dispatcher.py` yazılırken
- HITL interrupt'ı aşıldıktan sonra dağıtım mantığı eklenirken
- Kapasite kontrolü implemente edilirken

---

## Rules

- `interrupt_before=["dispatcher"]` ile HITL gate'i bu node'dadır.
- Dispatcher, onay gelmeden çalışmaz.
- Dosyaları `planned → reserved` yapar.
- `asyncio.Queue` ile worker'lara iş gönderir.
- `active_workers` sayısını kontrol eder.

---

## Guidelines

```python
# src/graph/nodes/dispatcher.py
async def dispatcher_node(state: OrchestratorState) -> OrchestratorState:
    # Onay kontrolü
    if state.get("approval_status") != "approved":
        logger.info("Onay bekleniyor, dispatcher duruyor")
        return {}
    
    # planned dosyaları bul
    file_registry = state.get("file_registry", {})
    planned_files = [
        path for path, status in file_registry.items()
        if status == "planned"
    ]
    
    if not planned_files:
        logger.info("Dispatcher: dağıtılacak dosya yok")
        return {"dispatch_complete": True}
    
    # Kapasite kontrolü
    active = len(state.get("active_workers", {}))
    available_slots = MAX_CONCURRENT_WORKERS - active
    batch = planned_files[:available_slots]
    
    # Dosyaları reserved yap
    updated_registry = dict(file_registry)
    queue_entries = []
    
    tasks = {t["task_id"]: t for t in state.get("tasks", [])}
    
    for file_path in batch:
        updated_registry[file_path] = "reserved"
        task = _find_task_for_file(file_path, tasks)
        entry = build_queue_entry(
            sprint_id=state["sprint_id"],
            task=task,
            file_path=file_path,
        )
        queue_entries.append(entry)
        logger.info(f"Dağıtıldı: {file_path}")
    
    return {
        "file_registry": updated_registry,
        "dispatch_queue": queue_entries,
    }
```

---

## References

- `interrupt-before-node-skill/SKILL.md` — HITL
- `queue-entry-construction-skill/SKILL.md` — kuyruk girişi
- `file-status-state-machine-skill/SKILL.md` — dosya durumu
