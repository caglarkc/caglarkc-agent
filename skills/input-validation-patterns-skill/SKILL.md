---
name: input-validation-patterns
description: Coder AI için — kullanıcıdan veya dış sistemden gelen verinin Pydantic ile doğrulanması; hatalı input'u erken yakalamak.
---

## Purpose

Doğrulanmamış input sistemi çökertir veya yanlış veri yazar.
Pydantic validator'lar input'u sınırda durdurur.
LLM çıktısı da dış input sayılır — mutlaka doğrulanmalı.

---

## When to Apply

- CLI argümanı işlenirken
- Telegram mesajı parse edilirken
- LLM JSON çıktısı alınırken
- API endpoint handler yazılırken

---

## Rules

- Zorunlu alan eksikse `ValidationError` fırlatılır — `None` geçilmez.
- String max uzunluk: 5000 karakter (task description için).
- `sprint_id` formatı: `sprint_` ile başlar.
- LLM çıktısı: `model_validate_json()` ile parse edilir.
- Geçersiz input: kullanıcıya anlaşılır hata mesajı döner.

---

## Guidelines

```python
from pydantic import BaseModel, Field, field_validator
import re

class CreateSprintRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=10, max_length=5000)
    tasks: list[str] = Field(min_length=1, max_length=20)

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("project_id sadece alfanumerik, _ ve - içerebilir")
        return v

# LLM çıktısı doğrulama
class LLMPlanOutput(BaseModel):
    tasks: list[TaskSchema]
    files: list[str]
    summary: str

async def parse_llm_response(raw_json: str) -> LLMPlanOutput:
    try:
        return LLMPlanOutput.model_validate_json(raw_json)
    except ValidationError as e:
        logger.error(f"LLM çıktısı doğrulanamadı: {e}")
        raise ValueError(f"LLM geçersiz JSON döndürdü: {e}") from e
```

CLI input doğrulama:
```python
def validate_project_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Proje adı boş olamaz")
    if len(name) > 100:
        raise ValueError("Proje adı 100 karakterden uzun olamaz")
    return name
```

---

## References

- `pydantic-model-design-skill/SKILL.md` — model tasarımı
- `llm-output-parsing-skill/SKILL.md` — LLM çıktı parse
- `settings-validation-skill/SKILL.md` — ayar doğrulama
