---
name: async-function-template
description: Coder AI için — bu projede her async fonksiyonun uyması gereken standart yapı; tip hint, hata handling, logging ve return formatı dahil.
---

## Purpose

Coder AI'ın yazdığı her async fonksiyonun tutarlı bir yapıya sahip olmasını sağlar.
Standart şablon sayesinde review kolaylaşır, eksikler azalır.

---

## When to Apply

- Yeni bir async fonksiyon yazılırken
- Mevcut sync fonksiyon async'e dönüştürülürken
- Node, servis metodu veya repository metodu yazılırken

---

## Rules

- Her async fonksiyon tip hint alır (parametre + dönüş).
- Dış çağrı (LLM, DB, HTTP) try/except ile sarılır.
- Başlangıç ve sonuç logger.debug ile kaydedilebilir (yüksek değer ise logger.info).
- `return` tipi document edilir (özellikle `dict[str, Any]` için ne içerdiği).
- Kaynaklar context manager ile açılır/kapatılır.

---

## Guidelines

Temel async fonksiyon şablonu:
```python
import logging
from typing import Any

logger = logging.getLogger(__name__)

async def function_name(
    param1: str,
    param2: dict[str, Any],
    optional_param: int = 0
) -> ResultType:
    """Kısa açıklama (sadece WHY non-obvious ise)."""
    logger.debug(f"function_name başladı: {param1}")
    
    try:
        result = await _do_something(param1, param2)
        logger.debug(f"function_name tamamlandı")
        return result
    except SpecificError as e:
        logger.error(f"function_name hatası: {e}", extra={"param1": param1})
        raise
```

LangGraph node şablonu:
```python
async def example_node(state: OrchestratorState) -> dict[str, Any]:
    logger.info(f"example_node başladı: {state['project_id']}")
    
    try:
        result = await service.process(state["task_description"])
        
        await event_bus.emit("example.completed", {
            "project_id": state["project_id"],
            "result": result
        })
        
        return {
            "messages": state.get("messages", []) + ["Example tamamlandı"],
            "example_result": result
        }
    except Exception as e:
        logger.exception(f"example_node hatası: {e}")
        return {
            "errors": state.get("errors", []) + [{
                "node": "example",
                "error": str(e)
            }]
        }
```

Repository metod şablonu:
```python
async def get_record(self, record_id: str) -> RecordModel | None:
    async with aiosqlite.connect(self.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM records WHERE id = ?", (record_id,)
        )
        row = await cursor.fetchone()
        return RecordModel(**dict(row)) if row else None
```

---

## References

- `code-mode-skill/SKILL.md` — genel kural seti
- `python-async-patterns-skill/SKILL.md` — async referans
- `exception-handling-review-skill/SKILL.md` — hata handling
