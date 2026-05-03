---
name: conditional-sprint-flow
description: Planner AI için — sprint içinde koşullu akış oluşturmak; belirli koşullar sağlanırsa farklı görev setleri yürütmek.
---

## Purpose

Her sprint doğrusal değil — "eğer test başarısızsa X, başarılıysa Y" gibi dallanmalar gerekebilir.
Koşullu akış, sprint planını esnek hâle getirir.
LangGraph'ın conditional edges'i bu amaçla kullanılır.

---

## When to Apply

- Test sonucuna göre farklı görevler tetiklenirken
- Kullanıcı onayına bağlı iki farklı yol varken
- Bir dosyanın varlığına göre skip/execute kararı verilirken

---

## Rules

- Koşul: sprint state'inden okunur, harici çağrı yapılmaz.
- Dal sayısı: maks 3 (basit tutulur).
- Varsayılan dal her zaman tanımlı olmalı.
- Koşullar task description'da belgelenir.

---

## Guidelines

```python
from typing import Literal

def route_after_test(
    state: dict,
) -> Literal["fix_code", "continue_sprint", "notify_user"]:
    test_result = state.get("last_test_result")
    if test_result == "passed":
        return "continue_sprint"
    elif test_result == "failed" and state.get("retry_count", 0) < 3:
        return "fix_code"
    else:
        return "notify_user"

# LangGraph conditional edge tanımı
def build_conditional_graph(builder):
    builder.add_conditional_edges(
        "validator",
        route_after_test,
        {
            "fix_code":       "worker",
            "continue_sprint": "reviewer",
            "notify_user":    "planner",
        },
    )

# Sprint plan koşullu görev yapısı
def plan_with_condition(condition: str, if_true: list, if_false: list) -> dict:
    return {
        "type": "conditional",
        "condition": condition,
        "if_true": if_true,
        "if_false": if_false,
    }

# Örnek kullanım
conditional_task = plan_with_condition(
    condition="file_exists:src/config.py",
    if_true=["update_config"],
    if_false=["create_config", "update_imports"],
)
```

---

## References

- `sprint-plan-revision-skill/SKILL.md` — plan revizyonu
- `graph-assembly-skill/SKILL.md` — graf montajı
- `task-dependency-ordering-skill/SKILL.md` — görev sıralaması
