---
name: test-data-builder
description: Coder AI için — test verisi üretmek için builder pattern kullanmak; her test için temiz, izole veri oluşturmak.
---

## Purpose

Test'ler aynı veriye bağımlı olursa birbirini bozar.
Builder pattern: her test için bağımsız, özelleştirilebilir veri üretir.
Fixture fabrikasından daha esnek — test bazlı ince ayar mümkün.

---

## When to Apply

- Karmaşık nesne yapısıyla test yazılırken
- Aynı nesnenin birden fazla varyasyonu test edilirken
- Faker veya factory_boy kullanılırken

---

## Rules

- Builder: her alan için metod zinciri (fluent API).
- Varsayılanlar: geçerli, minimal değerler.
- `.build()` son nesneyi döndürür.
- Paylaşılan builder'lar session fixture'a taşınır.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class Task:
    id: str
    description: str
    file_path: str
    status: str
    estimated_minutes: int
    depends_on: list[str]
    created_at: datetime

class TaskBuilder:
    def __init__(self):
        self._id          = str(uuid.uuid4())[:8]
        self._description = "Test görevi"
        self._file_path   = "src/test_file.py"
        self._status      = "planned"
        self._estimated   = 10
        self._depends_on: list[str] = []
        self._created_at  = datetime.utcnow()
    
    def with_id(self, id: str) -> "TaskBuilder":
        self._id = id; return self
    
    def with_description(self, desc: str) -> "TaskBuilder":
        self._description = desc; return self
    
    def with_file(self, path: str) -> "TaskBuilder":
        self._file_path = path; return self
    
    def with_status(self, status: str) -> "TaskBuilder":
        self._status = status; return self
    
    def depends_on(self, *ids: str) -> "TaskBuilder":
        self._depends_on = list(ids); return self
    
    def build(self) -> Task:
        return Task(
            id=self._id,
            description=self._description,
            file_path=self._file_path,
            status=self._status,
            estimated_minutes=self._estimated,
            depends_on=self._depends_on,
            created_at=self._created_at,
        )

# Kullanım
def test_dependency_ordering():
    task_a = TaskBuilder().with_id("a").build()
    task_b = TaskBuilder().with_id("b").depends_on("a").build()
    
    ordered = order_by_dependencies([task_a, task_b])
    assert ordered[0].id == "a"
    assert ordered[1].id == "b"
```

---

## References

- `fixture-factory-pattern-skill/SKILL.md` — fixture fabrikası
- `mock-repository-pattern-skill/SKILL.md` — mock repository
- `parametrize-test-cases-skill/SKILL.md` — parametrize testler
