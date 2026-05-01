---
name: pydantic-model-review
description: Planner AI için — Pydantic v2 model tanımlarının doğru alanlar, tipler ve validator'lar içerdiğini; proje veri modelleriyle tutarlı olduğunu review sırasında doğrulamak.
---

## Purpose

Pydantic model hatalarını review sırasında yakalar.
Yanlış tip, eksik validator, uyumsuz field default gibi sorunları tespit eder.
Storage modelleri ve kontrat modelleri arasındaki tutarlılığı kontrol eder.

---

## When to Apply

- `src/storage/models.py` veya `src/core/contracts.py` review edilirken
- Yeni Pydantic model eklenirken
- Model field'ı değiştirilirken

---

## Rules

- Pydantic v2 kullanılır — `@validator` değil `@field_validator` veya `model_validator`.
- `BaseModel` için `model_config = ConfigDict(...)` kullanılır.
- Zorunlu alanların default değeri olmaz.
- `str` ile saklanan enum değerleri için `use_enum_values=True` kullanılır.
- JSON serialize edilecek model: `model.model_dump_json()` kullanılır.
- `datetime` alanları `datetime` tipi, string'e serialize için `isoformat()`.
- ID alanları `str` (UUID string), `int` değil.

---

## Guidelines

Model kontrol:
```python
# DOĞRU Pydantic v2 model
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class FileRecord(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    path: str
    status: FileStatus = FileStatus.PLANNED
    worker_id: str | None = None
    attempt_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("path")
    @classmethod
    def path_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("path cannot be empty")
        return v

# YANLIŞ — Pydantic v1 stili
class FileRecord(BaseModel):
    @validator("path")  # v1 stili, v2'de çalışmaz
    def path_not_empty(cls, v):
        ...
```

BaseSettings kontrol:
```python
# DOĞRU
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    GEMINI_API_KEY: str  # zorunlu
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"  # opsiyonel, default var
    LOG_LEVEL: str = "INFO"
```

---

## References

- `database-schema-review-skill/SKILL.md` — storage modeller
- `interface-contract-review-skill/SKILL.md` — kontrat modeller
- `pydantic-v2-model-definition-skill/SKILL.md` — coder model tanımı
