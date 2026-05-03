---
name: conditional-edge-function
description: Coder AI için — LangGraph conditional edge fonksiyonlarını src/graph/edges.py'e doğru yazma; tüm case'leri kapsayan, pure function, string döndüren routing fonksiyonları.
---

## Purpose

Graph'ın hangi node'a gideceğini belirleyen routing fonksiyonlarını doğru yazar.
Eksik case'ler graph'ı dondurmaya yol açar.
Routing mantığı node içinde değil edges.py'de olmalıdır.

---

## When to Apply

- `src/graph/edges.py`'e yeni routing fonksiyonu eklenirken
- Mevcut routing mantığı değiştirilirken
- Graph akışına yeni dal (branch) eklenirken

---

## Rules

- Routing fonksiyonu: `def route_after_<node>(state: OrchestratorState) -> str`
- Dönüş: node adı (string) veya `END` (langgraph.constants'tan).
- Pure function: state okur ama değiştirmez.
- Tüm olası state kombinasyonları için return var olmalı.
- `else` veya default case zorunlu — `None` dönemez.
- `END` import: `from langgraph.constants import END`

---

## Guidelines

Standart edge fonksiyonu şablonu:
```python
from langgraph.constants import END
from src.graph.state import OrchestratorState


def route_after_planner(state: OrchestratorState) -> str:
    """Planner sonrası yönlendirme."""
    # Onay bekleniyor → dur
    if state.get("approval_request"):
        return END
    
    # Plan var → dispatcher'a git
    if state.get("draft_plan"):
        return "dispatcher"
    
    # Hata var → bitir
    if state.get("errors"):
        return END
    
    # Default: bitir
    return END


def route_after_validator(state: OrchestratorState) -> str:
    """Validator sonrası yönlendirme."""
    critical_issues = [
        i for i in state.get("validation_issues", [])
        if i.get("severity") == "error"
    ]
    
    if critical_issues:
        return "reviewer"
    
    # İş kaldı mı?
    pending = [
        q for q in state.get("worker_queue", [])
        if q.get("status") == "planned"
    ]
    if pending:
        return "dispatcher"
    
    return "reviewer"  # hepsi bitti, review
```

Graph'a bağlama:
```python
graph = StateGraph(OrchestratorState)
graph.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "dispatcher": "dispatcher",
        END: END
    }
)
```

---

## References

- `langgraph-edge-routing-review-skill/SKILL.md` — edge review
- `graph-builder-usage-skill/SKILL.md` — graph inşası
- `review-cycle-limit-enforcement-skill/SKILL.md` — döngü limiti
