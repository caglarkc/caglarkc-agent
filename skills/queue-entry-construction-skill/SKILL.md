---
name: queue-entry-construction
description: Coder AI için — dispatcher'ın worker'a gönderdiği iş kuyruğu girişini (QueueEntry) doğru alanlarla oluşturmak.
---

## Purpose

Dispatcher, worker'a ne yazacağını söyleyen bir paket gönderir.
Bu paketin eksik veya hatalı alanı olursa worker yanlış dosya yazar.
QueueEntry, dispatcher → worker arasındaki kontrat.

---

## When to Apply

- Dispatcher node'da worker'a iş atanırken
- `asyncio.Queue` veya EventBus'a mesaj koyulurken
- Worker task schema'sı tanımlanırken

---

## Rules

- `file_path` zorunlu — nereye yazılacağı belirsiz olamaz.
- `task_description` zorunlu — ne yazılacağı net olmalı.
- `context_files` opsiyonel — bağımlı dosyalar eklenebilir.
- `priority` varsayılan `"normal"` — acil görevler `"high"`.
- `QueueEntry` immutable olarak tasarlanır (frozen dataclass veya Pydantic).

---

## Guidelines

```python
from pydantic import BaseModel, Field
from typing import Literal
import uuid

class QueueEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sprint_id: str
    task_id: str
    file_path: str
    task_description: str
    context_files: list[str] = Field(default_factory=list)
    priority: Literal["high", "normal", "low"] = "normal"
    retry_count: int = 0
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    model_config = {"frozen": True}  # immutable


def build_queue_entry(
    sprint_id: str,
    task: dict,
    file_path: str,
    context_files: list[str] | None = None,
    priority: str = "normal"
) -> QueueEntry:
    return QueueEntry(
        sprint_id=sprint_id,
        task_id=task["task_id"],
        file_path=file_path,
        task_description=task.get("description", ""),
        context_files=context_files or task.get("dependencies", []),
        priority=priority,
    )
```

Dispatcher'da kullanım:
```python
for file_path in files_to_dispatch:
    entry = build_queue_entry(
        sprint_id=state["sprint_id"],
        task=current_task,
        file_path=file_path,
        context_files=current_task.get("dependencies", []),
    )
    await work_queue.put(entry)
    logger.debug(f"Kuyruğa eklendi: {file_path}")
```

---

## References

- `file-status-state-machine-skill/SKILL.md` — dosya rezervasyonu
- `worker-status-tracking-skill/SKILL.md` — worker takibi
- `dispatcher-node-implementation-skill/SKILL.md` — dispatcher
