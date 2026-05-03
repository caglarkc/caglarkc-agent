---
name: type-alias-definition
description: Coder AI için — karmaşık tip ifadelerini okunabilir tip alias'larıyla basitleştirmek; kodun self-documenting olmasını sağlamak.
---

## Purpose

`dict[str, dict[str, list[tuple[str, int]]]]` okunaksız.
Tip alias anlamlı isim verir ve tekrarı önler.
`FileRegistry = dict[str, str]` gibi alias, kodun niyetini açıklar.

---

## When to Apply

- Aynı karmaşık tip birden fazla yerde kullanıldığında
- `OrchestratorState` field tipleri tanımlanırken
- Callback veya handler fonksiyon tipleri belirtilirken

---

## Rules

- Python 3.10+: `type FileRegistry = dict[str, str]` (yeni syntax).
- Python 3.9: `FileRegistry = dict[str, str]` (eski syntax).
- TypeAlias: `from typing import TypeAlias` ile belirtilir.
- Generic alias: `type TaskList[T] = list[T]`.
- `src/core/types.py` dosyasına merkezi olarak konulur.

---

## Guidelines

```python
# src/core/types.py
from typing import TypeAlias

# Basit alias'lar
ProjectId: TypeAlias = str
SprintId: TypeAlias = str
FilePath: TypeAlias = str
FileStatus: TypeAlias = str

# Karmaşık alias'lar
FileRegistry: TypeAlias = dict[FilePath, FileStatus]
ActiveWorkers: TypeAlias = dict[str, dict]  # worker_id → WorkerInfo
TaskList: TypeAlias = list[dict]
DispatchQueue: TypeAlias = list[dict]

# Callback tipleri
EventHandler: TypeAlias = Callable[[dict], Awaitable[None]]
NodeFunction: TypeAlias = Callable[["OrchestratorState"], Awaitable["OrchestratorState"]]
```

OrchestratorState'de kullanım:
```python
from src.core.types import FileRegistry, TaskList, ActiveWorkers

class OrchestratorState(TypedDict):
    file_registry: FileRegistry
    tasks: TaskList
    active_workers: ActiveWorkers
    project_id: ProjectId
    sprint_id: SprintId | None
```

---

## References

- `state-typeddict-definition-skill/SKILL.md` — state tanımı
- `type-annotation-patterns-skill/SKILL.md` — tip ipuçları (henüz yok)
- `pydantic-v2-model-definition-skill/SKILL.md` — model tipler
