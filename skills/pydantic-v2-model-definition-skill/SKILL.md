---
name: pydantic-v2-model-definition
description: Coder AI için — bu projede Pydantic v2 ile model tanımlamanın doğru yolu; field tanımları, validator'lar, enum entegrasyonu ve JSON serialization.
---

## Purpose

Pydantic v2 API'sını doğru kullanmayı sağlar.
v1 ve v2 arasındaki API farkları (validator → field_validator, dict() → model_dump()) hata kaynağıdır.
Tutarlı model tanımı review ve test süreçlerini hızlandırır.

---

## When to Apply

- `src/storage/models.py` veya `src/core/contracts.py` için yeni model yazılırken
- Var olan modele alan eklenirken
- JSON serialization gereken model oluşturulurken

---

## Rules

- `from pydantic import BaseModel, Field, field_validator, model_validator` kullanılır.
- `ConfigDict` ile model konfigürasyonu yapılır.
- Zorunlu alan: default değer verilmez.
- Opsiyonel alan: `X | None = None` veya `Field(default=None)`.
- JSON serialize: `model.model_dump()` veya `model.model_dump_json()`.
- `validator` değil `field_validator` (v2 API).
- `__fields__` değil `model_fields` (v2 API).

---

## Guidelines

Eksiksiz model örneği:
```python
from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


class FileStatus(str, Enum):
    PLANNED = "planned"
    RESERVED = "reserved"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class FileRecord(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        validate_assignment=True
    )
    
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    path: str
    status: FileStatus = FileStatus.PLANNED
    worker_id: str | None = None
    attempt_count: int = Field(default=0, ge=0)
    last_error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("path")
    @classmethod
    def path_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("path boş olamaz")
        return v.strip()
    
    def to_db_dict(self) -> dict:
        d = self.model_dump()
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d
    
    @classmethod
    def from_db_row(cls, row: dict) -> FileRecord:
        row["created_at"] = datetime.fromisoformat(row["created_at"])
        row["updated_at"] = datetime.fromisoformat(row["updated_at"])
        return cls(**row)
```

---

## References

- `pydantic-model-review-skill/SKILL.md` — model review kriterleri
- `database-schema-review-skill/SKILL.md` — DB ile uyum
- `enum-definition-skill/SKILL.md` — enum kullanımı
