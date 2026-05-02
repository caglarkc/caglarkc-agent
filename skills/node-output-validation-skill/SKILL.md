---
name: node-output-validation
description: Coder AI için — LangGraph node'unun döndürdüğü state update'ini doğrulamak; zorunlu alanların mevcut ve doğru tipte olduğunu kontrol etmek.
---

## Purpose

Node yanlış tip veya eksik alan döndürürse sonraki node hata verir.
Output validation hataları erken yakalar ve anlamlı mesaj üretir.
Özellikle LLM tabanlı node'larda çıktı tutarsızlıkları sık görülür.

---

## When to Apply

- Node implementation yazılırken output kontrolü eklenirken
- LLM çıktısından state update üretilirken
- Node test edilirken output şeması doğrulanırken

---

## Rules

- Her node Pydantic ile output doğrular (opsiyonel ama önerilir).
- Zorunlu alan dönmezse: `NodeOutputError` fırlatılır.
- Tip hatası: log + default değer kullanılır (kritik değilse).
- Test'te output şeması assertion ile kontrol edilir.

---

## Guidelines

```python
from pydantic import BaseModel, field_validator

class PlannerNodeOutput(BaseModel):
    sprint_id: str
    tasks: list[dict]
    file_registry: dict[str, str]
    sprint_summary: str = ""

    @field_validator("tasks")
    @classmethod
    def validate_tasks_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("Planner en az 1 görev üretmeli")
        return v
    
    @field_validator("file_registry")
    @classmethod
    def validate_all_planned(cls, v: dict) -> dict:
        invalid = {k for k, s in v.items() if s != "planned"}
        if invalid:
            raise ValueError(f"Tüm dosyalar 'planned' olmalı: {invalid}")
        return v

class NodeOutputError(Exception):
    pass

def validate_node_output(
    output: dict,
    model_class: type[BaseModel],
    node_name: str,
) -> BaseModel:
    try:
        return model_class.model_validate(output)
    except ValidationError as e:
        raise NodeOutputError(
            f"{node_name} geçersiz output: {e}"
        ) from e

# Planner node'da kullanım
async def planner_node(state: OrchestratorState) -> OrchestratorState:
    ...
    raw_output = {
        "sprint_id": sprint_id,
        "tasks": tasks,
        "file_registry": file_registry,
    }
    validated = validate_node_output(raw_output, PlannerNodeOutput, "planner")
    return validated.model_dump()
```

---

## References

- `node-function-signature-skill/SKILL.md` — node imzası
- `input-validation-patterns-skill/SKILL.md` — doğrulama
- `planner-node-implementation-skill/SKILL.md` — planner
