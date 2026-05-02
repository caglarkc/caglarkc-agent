---
name: node-error-boundary
description: Coder AI için — LangGraph node'larını hata sınırıyla sarmak; node hatası grafı çökermesin.
---

## Purpose

Bir node'daki hata tüm LangGraph akışını durdurabilir.
Error boundary: hata yakalanır, state'e güvenli şekilde kaydedilir, akış devam eder.
Hangi node'un neden hata verdiği izlenebilir olur.

---

## When to Apply

- Her production LangGraph node'una güvenli sarmalayıcı eklenirken
- Node hatası sonrası graceful degradation isteniyor
- Hata state'ini kayıt altına alma zorunluyken

---

## Rules

- Sarmalayıcı: `try/except` + state güncelleme + log.
- Yakalanan hata: `node_errors` listesine eklenir.
- `Exception` türü dışında sistemin bilmediği hatalara `UNKNOWN` denir.
- Kritik node (planner): hata → kullanıcıya bildirim.

---

## Guidelines

```python
import logging
import traceback
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def node_error_boundary(
    node_name: str,
    critical: bool = False,
):
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(state: dict, *args, **kwargs) -> dict:
            try:
                return await fn(state, *args, **kwargs)
            except Exception as exc:
                tb = traceback.format_exc()
                logger.error("[%s] Node hatası: %s\n%s", node_name, exc, tb)
                
                errors = list(state.get("node_errors", []))
                errors.append({
                    "node":    node_name,
                    "error":   str(exc),
                    "type":    type(exc).__name__,
                    "critical": critical,
                })
                
                update = {"node_errors": errors}
                if critical:
                    update["sprint_status"] = "failed"
                    update["failure_reason"] = f"{node_name}: {exc}"
                
                return update
        return wrapper
    return decorator

# Kullanım
@node_error_boundary("worker", critical=False)
async def worker_node(state: dict) -> dict:
    # ... worker mantığı
    return {}

@node_error_boundary("planner", critical=True)
async def planner_node(state: dict) -> dict:
    # ... planner mantığı
    return {}
```

---

## References

- `cascading-failure-prevention-skill/SKILL.md` — hata yayılma önleme
- `error-categorization-skill/SKILL.md` — hata kategorileme
- `graceful-degradation-skill/SKILL.md` — zarif bozulma
