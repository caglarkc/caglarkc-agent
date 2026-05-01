---
name: node-function-signature
description: Coder AI için — LangGraph node fonksiyonlarının doğru imzası, state okuma/yazma pattern'ı ve event emit entegrasyonu.
---

## Purpose

Her node'un LangGraph ile uyumlu doğru imzaya sahip olmasını sağlar.
State okuma ve kısmi güncelleme döndürme pattern'ını standartlaştırır.
Node sorumluluklarını net sınırlar içinde tutar.

---

## When to Apply

- Yeni LangGraph node fonksiyonu yazılırken
- Mevcut node'a yeni alan eklenmesi gerektiğinde
- Node içinde hangi state alanına dokunulacağı planlanırken

---

## Rules

- İmza: `async def <name>_node(state: OrchestratorState) -> dict[str, Any]`
- Sadece değişen state alanları döndürülür.
- State mutasyonu yasak — yeni dict döndürülür.
- `state["key"]` yerine `state.get("key", default)` tercih edilir (total=False için).
- Node hata aldığında `errors` listesine ekleme döndürülür, exception fırlatılmaz (graph durable olmalı).
- Event emit her node'da `await event_bus.emit(...)` ile yapılır.

---

## Guidelines

Standart node şablonu:
```python
import logging
from typing import Any
from src.graph.state import OrchestratorState
from src.core.event_bus import get_event_bus

logger = logging.getLogger(__name__)


async def example_node(state: OrchestratorState) -> dict[str, Any]:
    project_id = state.get("project_id", "unknown")
    logger.info(f"example_node başladı", extra={"project_id": project_id})
    
    event_bus = get_event_bus()
    
    try:
        # İş mantığı
        result = await _do_work(state)
        
        await event_bus.emit("example.completed", {
            "project_id": project_id,
            "result_summary": str(result)[:100]
        })
        
        return {
            "example_result": result,
            "messages": state.get("messages", []) + [
                f"Example tamamlandı: {result}"
            ]
        }
    
    except Exception as e:
        logger.exception(f"example_node hatası: {e}")
        await event_bus.emit("error.occurred", {
            "node": "example",
            "error": str(e),
            "project_id": project_id
        })
        return {
            "errors": state.get("errors", []) + [{
                "node": "example_node",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
```

State okuma güvenli:
```python
# total=False TypedDict için .get() zorunlu
queue = state.get("worker_queue", [])
plan = state.get("draft_plan")  # None olabilir
cycles = state.get("review_cycles", 0)
```

---

## References

- `state-typeddict-definition-skill/SKILL.md` — state şeması
- `state-update-return-pattern-skill/SKILL.md` — güncelleme pattern
- `langgraph-patterns-skill/SKILL.md` — LangGraph kuralları
