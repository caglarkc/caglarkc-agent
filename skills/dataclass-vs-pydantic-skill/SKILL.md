---
name: dataclass-vs-pydantic
description: Coder AI için — ne zaman Python dataclass ne zaman Pydantic model kullanılacağını belirlemek; her ikisinin güçlü yönlerini doğru senaryoda uygulamak.
---

## Purpose

Her şey için Pydantic kullanmak gereksiz overhead yaratır.
Her şey için dataclass kullanmak doğrulama boşluğu oluşturur.
Doğru araç: doğrulama gerekiyorsa Pydantic, iç veri yapısı için dataclass.

---

## When to Apply

- Yeni model sınıfı tanımlanırken hangi temel sınıf seçileceğine karar verilirken
- DB model veya API request/response nesnesi tasarlanırken
- İç state veya geçici veri yapısı yazılırken

---

## Rules

- **Pydantic**: DB model, API input/output, settings, LLM çıktı şeması.
- **Dataclass**: iç hesaplama nesneleri, geçici state, test yardımcıları.
- **NamedTuple**: read-only basit veri grupları.
- Pydantic `BaseModel`: `frozen=True` ile immutable yapılabilir.
- Dataclass: `@dataclass(frozen=True)` ile immutable.

---

## Guidelines

```python
# ✓ Pydantic — DB modeli, doğrulama ve serialization gerekli
class Sprint(BaseModel):
    sprint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    status: SprintStatus = SprintStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"use_enum_values": True}

# ✓ Dataclass — iç hesaplama nesnesi
@dataclass
class RecoveryPlan:
    skip: list[str]
    reset_to_planned: list[str]
    retry: list[str]

# ✓ Dataclass frozen — değişmemesi gereken iç nesne
@dataclass(frozen=True)
class WorkerResult:
    worker_id: str
    file_path: str
    success: bool
    error: str | None = None

# ✓ NamedTuple — basit gruplar
from typing import NamedTuple

class ProviderConfig(NamedTuple):
    name: str
    base_url: str
    api_key: str
```

Karar ağacı:
```
Dış input veya DB? → Pydantic
Validation gerekli? → Pydantic
Sadece iç veri grubu? → dataclass
Read-only basit tuple? → NamedTuple
```

---

## References

- `pydantic-v2-model-definition-skill/SKILL.md` — Pydantic modeli
- `state-typeddict-definition-skill/SKILL.md` — TypedDict state
- `input-validation-patterns-skill/SKILL.md` — doğrulama
