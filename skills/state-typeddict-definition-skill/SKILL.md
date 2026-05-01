---
name: state-typeddict-definition
description: Coder AI için — LangGraph OrchestratorState TypedDict şemasına yeni alan eklemenin ve mevcut alanları düzenlemenin doğru yolu.
---

## Purpose

`src/graph/state.py`'deki OrchestratorState şemasını doğru biçimde genişletir.
LangGraph'ta state alanlarının reducer fonksiyonu gerektirip gerektirmediğini belirler.
State şeması değişikliği tüm node'ları etkiler — dikkatli tasarım şarttır.

---

## When to Apply

- Yeni state alanı ekleneceğinde
- Mevcut alan tipi değiştirilirken
- Reducer fonksiyonu gerektiren liste/dict alanı eklenirken

---

## Rules

- State alanları `TypedDict` veya `Annotated` ile tanımlanır.
- Liste alanları reducer gerektirir: `Annotated[list, add_messages]` gibi.
- Yeni alan eklemek contract sprint gerektirir.
- Tüm alanların `total=False` veya default değeri olmalı (node'lar kısmi güncelleme yapar).
- `build_initial_state()` fonksiyonu yeni alan ile güncellenmeli.

---

## Guidelines

Temel TypedDict şeması:
```python
from typing import TypedDict, Annotated, Any
from operator import add


class OrchestratorState(TypedDict, total=False):
    # Proje kimlik bilgileri
    project_id: str
    project_name: str
    task_description: str
    
    # Planlama
    draft_plan: dict[str, Any] | None
    conversation_history: list[dict[str, str]]
    approval_request: dict[str, Any] | None
    
    # Execution
    worker_queue: list[dict[str, Any]]
    file_registry: dict[str, str]  # path → status
    worker_status: dict[str, str]  # worker_id → status
    
    # Validation
    validation_issues: list[dict[str, Any]]
    review_cycles: int
    
    # Tracking
    messages: list[str]
    errors: list[dict[str, Any]]
    sprint_id: str | None
```

Reducer gerektiren alan:
```python
# Liste birleştirme için add reducer
from operator import add
from typing import Annotated

class OrchestratorState(TypedDict, total=False):
    # Her node kendi mesajlarını ekler, mevcut liste korunur
    messages: Annotated[list[str], add]
    
    # Normal alan — node'un döndürdüğü değer direkt set edilir
    draft_plan: dict[str, Any] | None
```

`build_initial_state()` güncelleme:
```python
def build_initial_state(project_id: str, task: str) -> OrchestratorState:
    return OrchestratorState(
        project_id=project_id,
        task_description=task,
        draft_plan=None,
        worker_queue=[],
        file_registry={},
        worker_status={"worker_a": "idle", "worker_b": "idle", "worker_c": "idle"},
        validation_issues=[],
        review_cycles=0,
        messages=[],
        errors=[],
        # Yeni alan buraya eklenir
        new_field=default_value,
    )
```

---

## References

- `langgraph-patterns-skill/SKILL.md` — LangGraph şema kuralları
- `node-function-signature-skill/SKILL.md` — node imzası
- `state-machine-design-review-skill/SKILL.md` — state review
