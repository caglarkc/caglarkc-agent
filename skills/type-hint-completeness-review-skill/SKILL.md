---
name: type-hint-completeness-review
description: Planner AI için — Coder AI çıktısında tüm fonksiyon parametrelerinin ve dönüş tiplerinin type hint ile annotate edildiğini review sırasında kontrol etmek.
---

## Purpose

Type hint eksikliğini review sırasında yakalar.
Dönüş tipi belirsiz fonksiyonlar hata ayıklamayı zorlaştırır.
Pydantic ve LangGraph bu proje için tip güvenliğine kritik bağımlıdır.

---

## When to Apply

- Her Coder AI kodu review'ında zorunlu
- Yeni fonksiyon veya metod eklendiğinde
- Refactoring sonrası kontrol

---

## Rules

- Tüm fonksiyon parametreleri type hint almalı.
- Dönüş tipi her fonksiyonda belirtilmeli (`-> None` dahil).
- `Any` kullanımı minimumda tutulmalı — gerçekten belirsizse `Any`, değilse spesifik tip.
- `dict` yerine `dict[str, Any]` veya spesifik TypedDict.
- `list` yerine `list[str]` gibi parameterized tip.
- `Optional[X]` yerine `X | None` tercih edilir (Python 3.10+).
- Pydantic model field'ları için `Field()` ile açıklama eklenebilir.

---

## Guidelines

Eksik type hint tespiti:
```python
# YANLIŞ — type hint eksik
def process_plan(plan, project_id):
    return plan["files"]

# DOĞRU
def process_plan(
    plan: dict[str, Any],
    project_id: str
) -> list[str]:
    return plan["files"]
```

Node dönüş tipi:
```python
# YANLIŞ
async def planner_node(state):  # tip yok
    return {}

# DOĞRU
async def planner_node(state: OrchestratorState) -> dict[str, Any]:
    return {"draft_plan": plan}
```

Optional kullanımı:
```python
# Python 3.10+ tercih
def find_record(file_id: str) -> FileRecord | None:
    ...

# Eski stil (kabul edilebilir ama önerilmez)
from typing import Optional
def find_record(file_id: str) -> Optional[FileRecord]:
    ...
```

Yaygın tipler bu projede:
```python
OrchestratorState          # LangGraph state
dict[str, Any]             # generic state update
list[QueueEntry]           # worker queue
dict[str, str]             # file_registry
str | None                 # optional string
list[dict[str, Any]]       # messages, errors
```

---

## References

- `code-mode-skill/SKILL.md` — type hint zorunluluğu
- `pydantic-model-review-skill/SKILL.md` — model tip kontrolü
- `interface-contract-review-skill/SKILL.md` — imza doğrulama
