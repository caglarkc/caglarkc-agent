---
name: thread-config-usage
description: Coder AI için — LangGraph thread konfigürasyonunu doğru oluşturmak ve checkpointer'ın doğru thread'i bulmasını sağlamak.
---

## Purpose

LangGraph, checkpoint'i thread_id ile eşleştirir.
Yanlış thread_id farklı projenin state'ini döndürür veya hiçbir şey bulamaz.
`project_id` → `thread_id` eşlemesi tutarlı olmalı.

---

## When to Apply

- `ainvoke`, `aget_state`, `aupdate_state` çağrıları yazılırken
- `src/graph/config.py` thread config yardımcısı oluşturulurken
- Multi-project desteği implemente edilirken

---

## Rules

- `thread_id = project_id` — basit ve tutarlı.
- `checkpoint_ns`: namespace gerekiyorsa kullanılır (opsiyonel).
- Config dict: her LangGraph çağrısında aynı yapı.
- Thread_id değiştirme: yeni sprint başlangıcında — gerekirse.

---

## Guidelines

```python
# src/graph/config.py
from typing import TypedDict

class LangGraphConfig(TypedDict):
    configurable: dict

def get_thread_config(
    project_id: str,
    checkpoint_ns: str = "",
) -> LangGraphConfig:
    config: dict = {"thread_id": project_id}
    if checkpoint_ns:
        config["checkpoint_ns"] = checkpoint_ns
    return {"configurable": config}

# Kullanım
config = get_thread_config("my-project")

# Graph başlatma
await compiled.ainvoke(initial_state, config=config)

# State okuma
snapshot = await compiled.aget_state(config=config)

# State güncelleme
await compiled.aupdate_state(
    config=config,
    values={"approval_status": "approved"},
)

# Resume
await compiled.ainvoke(None, config=config)
```

Multi-sprint desteği:
```python
def get_sprint_config(
    project_id: str,
    sprint_id: str,
) -> LangGraphConfig:
    # Sprint'e özgü checkpoint için
    return {"configurable": {
        "thread_id": f"{project_id}:{sprint_id}"
    }}
```

---

## References

- `thread-config-management-skill/SKILL.md` — mevcut thread config
- `graph-state-inspection-skill/SKILL.md` — state okuma
- `partial-sprint-recovery-skill/SKILL.md` — recovery
