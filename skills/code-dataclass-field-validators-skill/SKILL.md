---
name: code-dataclass-field-validators
description: Coder AI için — Python dataclass alanlarında __post_init__ ile doğrulama yapmak; geçersiz veri nesnesi oluşmasını önlemek.
---

## Purpose

Dataclass varsayılan olarak alan doğrulaması yapmaz.
`__post_init__`: nesne oluşturulunca çalışır, geçersiz değer hata fırlatır.
Pydantic'e gerek olmadan temel doğrulama dataclass içinde kalır.

---

## When to Apply

- Task, Sprint, WorkerState gibi veri nesneleri tanımlanırken
- Alan değerlerinde kısıt varken (pozitif sayı, izin verilen değerler)
- Pydantic bağımlılığı istemeden doğrulama gerektiğinde

---

## Rules

- `__post_init__`: dataclass constructor'dan sonra çalışır.
- Hata: `ValueError` fırlat, custom exception değil.
- Zorunlu format: tarih, UUID gibi alanlar normalize edilir.
- `field(default_factory=...)`: mutable varsayılan için.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime
import uuid

VALID_STATUSES = {"planned", "in_progress", "done", "failed", "cancelled"}
VALID_PRIORITIES = {1, 2, 3, 4, 5}

@dataclass
class Task:
    id:                str
    description:       str
    file_path:         str
    status:            str = "planned"
    priority:          int = 3
    estimated_minutes: int = 20
    depends_on:        list[str] = field(default_factory=list)
    created_at:        str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

        if not self.description.strip():
            raise ValueError("description boş olamaz")

        if not self.file_path.endswith(".py"):
            raise ValueError(f"file_path .py ile bitmeli: {self.file_path}")

        if self.status not in VALID_STATUSES:
            raise ValueError(f"Geçersiz status: {self.status}. İzin verilenler: {VALID_STATUSES}")

        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"Geçersiz priority: {self.priority}. 1-5 arası olmalı")

        if self.estimated_minutes <= 0:
            raise ValueError("estimated_minutes pozitif olmalı")

        # Normalize
        self.file_path = self.file_path.replace("\\", "/")

@dataclass
class SprintConfig:
    sprint_id:       str
    goal:            str
    max_workers:     int = 3
    max_tokens:      int = 500_000
    sprint_minutes:  int = 60

    def __post_init__(self):
        if self.max_workers < 1 or self.max_workers > 10:
            raise ValueError("max_workers 1-10 arasında olmalı")
        if not self.goal.strip():
            raise ValueError("goal boş olamaz")
```

---

## References

- `dataclass-vs-pydantic-skill/SKILL.md` — dataclass vs pydantic
- `input-validation-patterns-skill/SKILL.md` — giriş doğrulama
- `settings-validation-skill/SKILL.md` — ayar doğrulama
