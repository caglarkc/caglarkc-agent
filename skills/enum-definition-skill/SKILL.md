---
name: enum-definition
description: Coder AI için — bu projede string enum'ların doğru tanımlanma yolu; FileStatus, WorkerStatus gibi mevcut enum'larla tutarlı yapı.
---

## Purpose

String değerleri enum ile tip güvenliğine kavuşturur.
`"planned"`, `"done"` gibi literal string'ler yerine `FileStatus.PLANNED` kullanımı hata riskini azaltır.
Pydantic ve aiosqlite ile uyumlu enum tanımı sağlar.

---

## When to Apply

- Sabit string değer seti olan durum, tip veya kategori tanımlanırken
- Hardcode string magic value tespit edildiğinde
- Yeni state veya status alanı eklenirken

---

## Rules

- Status enum'ları `str, Enum` çoklu kalıtımla tanımlanır (JSON/DB uyumluluğu için).
- Enum değerleri lowercase snake_case string.
- `use_enum_values=True` ile Pydantic model'e entegre edilir.
- DB'de enum string olarak saklanır (`TEXT` kolonu).
- Yeni enum değeri eklemek breaking change sayılır → önce contract sprint.

---

## Guidelines

Standart enum tanımı:
```python
from enum import Enum


class FileStatus(str, Enum):
    PLANNED = "planned"
    RESERVED = "reserved"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class WorkerStatus(str, Enum):
    IDLE = "idle"
    RESERVED = "reserved"
    WORKING = "working"


class SprintType(str, Enum):
    CONTRACT = "contract"
    FEATURE = "feature"


class SprintStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

Kullanım:
```python
# Pydantic modelde
class FileRecord(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    status: FileStatus = FileStatus.PLANNED

# Karşılaştırma
if record.status == FileStatus.DONE:  # string ise: record.status == "done"
    ...

# DB'den okuma
status = FileStatus(row["status"])  # "done" → FileStatus.DONE
```

---

## References

- `pydantic-v2-model-definition-skill/SKILL.md` — model entegrasyonu
- `state-machine-design-review-skill/SKILL.md` — geçiş kuralları
- `magic-number-review-skill/SKILL.md` — hardcode string
