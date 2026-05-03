---
name: graph-state-reset
description: Coder AI için — LangGraph state'ini belirli alanları koruyarak kısmen sıfırlamak; yeni sprint başlangıcında önceki sprint'in çöp alanlarını temizlemek.
---

## Purpose

Yeni sprint başladığında önceki sprint'in `file_registry`, `tasks`, `dispatch_queue` alanları temizlenmeli.
Tüm state sıfırlanırsa `project_id` gibi kalıcı veriler kaybolur.
Kısmi sıfırlama: kalıcı alanlar korunur, sprint alanları sıfırlanır.

---

## When to Apply

- Sprint tamamlandıktan sonra yeni sprint başlatılırken
- Sprint cancel/fail sonrası yeniden başlamak için
- `aupdate_state` ile seçici state güncelleme yapılırken

---

## Rules

- `project_id`: asla sıfırlanmaz.
- `messages`: korunur (konuşma geçmişi).
- `sprint_id`, `file_registry`, `tasks`, `dispatch_queue`, `active_workers`: sıfırlanır.
- `review_count`, `approval_status`: sıfırlanır.
- `decisions` ve DB verileri state'de değil — state sıfırlama etkilemez.

---

## Guidelines

```python
SPRINT_FIELDS_TO_RESET = {
    "sprint_id": None,
    "file_registry": {},
    "tasks": [],
    "dispatch_queue": [],
    "active_workers": {},
    "approval_status": "pending",
    "review_result": None,
    "review_comments": [],
    "review_count": 0,
    "sprint_summary": "",
    "validation_passed": False,
    "dispatch_complete": False,
    "sprint_paused": False,
}

async def reset_sprint_state(
    compiled_graph,
    project_id: str,
) -> None:
    config = get_thread_config(project_id)
    
    # Mevcut state'i al
    snapshot = await compiled_graph.aget_state(config=config)
    current = snapshot.values if snapshot else {}
    
    # Sadece sprint alanlarını sıfırla
    await compiled_graph.aupdate_state(
        config=config,
        values=SPRINT_FIELDS_TO_RESET,
    )
    
    logger.info(f"Sprint state sıfırlandı: {project_id}")

# Yeni sprint başlatmadan önce
async def start_new_sprint(
    project_id: str,
    user_message: str,
    compiled_graph,
) -> None:
    await reset_sprint_state(compiled_graph, project_id)
    
    # Yeni sprint için planner başlat
    config = get_thread_config(project_id)
    await compiled_graph.aupdate_state(
        config=config,
        values={"messages": [HumanMessage(content=user_message)]},
    )
    await compiled_graph.ainvoke(None, config=config)
```

---

## References

- `state-initialization-skill/SKILL.md` — state başlatma
- `sprint-restart-skill/SKILL.md` — sprint yeniden başlatma
- `graph-state-inspection-skill/SKILL.md` — state okuma
