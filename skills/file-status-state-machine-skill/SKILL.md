---
name: file-status-state-machine
description: Coder AI için — file_registry içindeki dosya durumlarının geçerli geçişlerini (planned → reserved → in_progress → done/failed) zorlamak.
---

## Purpose

Dosya durumu keyfi değiştirilemez — race condition ve veri kaybına yol açar.
State machine hangi geçişin geçerli olduğunu zorlar.
`done` dosya tekrar `in_progress` yapılamaz.

---

## When to Apply

- Dispatcher `reserved` yaparken
- Worker `in_progress` veya `done` yaparken
- Recovery sırasında `in_progress` → `planned`'a geri alınırken

---

## Rules

- `done` terminal durum — üzerine yazılamaz.
- `failed` durumdan retry için `planned`'a geçiş mümkün (max_retries'a kadar).
- Geçersiz geçiş hata fırlatır — sessizce geçilmez.
- Geçiş anında `file_registry` dict güncellenir.

---

## Guidelines

```python
from enum import Enum

class FileStatus(str, Enum):
    PLANNED     = "planned"
    RESERVED    = "reserved"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    FAILED      = "failed"

VALID_FILE_TRANSITIONS: dict[FileStatus, set[FileStatus]] = {
    FileStatus.PLANNED:     {FileStatus.RESERVED},
    FileStatus.RESERVED:    {FileStatus.IN_PROGRESS, FileStatus.PLANNED},  # dispatcher cancel
    FileStatus.IN_PROGRESS: {FileStatus.DONE, FileStatus.FAILED},
    FileStatus.DONE:        set(),   # terminal
    FileStatus.FAILED:      {FileStatus.PLANNED},   # retry için
}

class InvalidFileTransition(Exception):
    pass

def transition_file_status(
    file_path: str,
    registry: dict[str, str],
    target: FileStatus
) -> dict[str, str]:
    current_raw = registry.get(file_path, FileStatus.PLANNED.value)
    current = FileStatus(current_raw)
    
    if target not in VALID_FILE_TRANSITIONS[current]:
        raise InvalidFileTransition(
            f"{file_path}: {current} → {target} geçersiz"
        )
    
    updated = dict(registry)
    updated[file_path] = target.value
    return updated
```

Dispatcher kullanımı:
```python
# Dosyayı rezerve et
file_registry = transition_file_status(
    file_path, state["file_registry"], FileStatus.RESERVED
)
```

---

## References

- `partial-sprint-recovery-skill/SKILL.md` — recovery reset
- `worker-status-tracking-skill/SKILL.md` — worker durumu
- `queue-entry-construction-skill/SKILL.md` — kuyruk oluşturma
