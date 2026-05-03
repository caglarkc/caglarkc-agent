---
name: code-enum-patterns
description: Coder AI için — Python Enum sınıflarını doğru kullanmak; string literal yerine tip güvenli sabitler tanımlamak.
---

## Purpose

`"planned"`, `"done"` gibi string literaller typo'ya açıktır.
Enum: geçerli değerleri kümeler, IDE tamamlar, mypy doğrular.
StrEnum (Python 3.11+): string ile karşılaştırma geriye dönük uyumlu.

---

## When to Apply

- Sabit değerler kümesi tanımlanırken (durum, tip, kategori)
- State machine geçişleri modellenmesinde
- DB veya API'den gelen kategori değerleri eşlenirken

---

## Rules

- Durum makinesi: StrEnum tercih edilir (JSON serialize kolay).
- Grup: ilgili sabitler aynı Enum'da.
- Bilinmeyen değer: `_missing_` ile ele al.
- Karşılaştırma: `status == TaskStatus.DONE` — string değil.

---

## Guidelines

```python
from enum import StrEnum, auto

class TaskStatus(StrEnum):
    PLANNED     = "planned"
    RESERVED    = "reserved"
    IN_PROGRESS = "in_progress"
    DONE        = "done"
    FAILED      = "failed"
    CANCELLED   = "cancelled"
    DEFERRED    = "deferred"

class SprintStatus(StrEnum):
    PLANNING   = "planning"
    APPROVED   = "approved"
    RUNNING    = "running"
    PAUSED     = "paused"
    COMPLETED  = "completed"
    FAILED     = "failed"
    ABORTED    = "aborted"
    CANCELLED  = "cancelled"

class NoteType(StrEnum):
    OBSERVATION = "observation"
    DECISION    = "decision"
    BLOCKER     = "blocker"
    LESSON      = "lesson"

# _missing_: bilinmeyen değeri ele al
class SafeTaskStatus(StrEnum):
    PLANNED = "planned"
    DONE    = "done"
    FAILED  = "failed"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN

# Geçiş kuralları
VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PLANNED:     {TaskStatus.RESERVED, TaskStatus.CANCELLED},
    TaskStatus.RESERVED:    {TaskStatus.IN_PROGRESS, TaskStatus.PLANNED},
    TaskStatus.IN_PROGRESS: {TaskStatus.DONE, TaskStatus.FAILED},
    TaskStatus.FAILED:      {TaskStatus.PLANNED},
    TaskStatus.DONE:        set(),
}

def can_transition(current: TaskStatus, next_: TaskStatus) -> bool:
    return next_ in VALID_TRANSITIONS.get(current, set())
```

---

## References

- `file-status-state-machine-skill/SKILL.md` — dosya durum makinesi
- `sprint-lifecycle-state-machine-skill/SKILL.md` — sprint durum makinesi
- `type-alias-definition-skill/SKILL.md` — tip takma adı
