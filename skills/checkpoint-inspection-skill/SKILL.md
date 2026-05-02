---
name: checkpoint-inspection
description: Coder AI için — LangGraph checkpoint'te saklanan state'i okuyarak mevcut sprint durumunu analiz etmek; hata ayıklama ve recovery için.
---

## Purpose

"Sprint nerede takıldı?" sorusunu yanıtlamak için checkpoint okunur.
Checkpoint, graph'ın son bilinen durumunu içerir.
Recovery, checkpoint analizi olmadan doğru yapılamaz.

---

## When to Apply

- Daemon restart sonrası sprint durumu kontrol edilirken
- Hata ayıklama sırasında state içeriği incelenirken
- `partial-sprint-recovery` öncesinde state analizi yapılırken

---

## Rules

- `aget_state(config)`: son checkpoint'i döndürür.
- `aget_state_history(config)`: tüm checkpoint geçmişi.
- Checkpoint yoksa: `None` veya boş snapshot.
- Debug modunda state içeriği log'a yazılır.

---

## Guidelines

```python
from langgraph.checkpoint.base import CheckpointMetadata

async def inspect_checkpoint(
    compiled_graph,
    project_id: str,
) -> dict | None:
    config = get_thread_config(project_id)
    
    try:
        snapshot = await compiled_graph.aget_state(config=config)
    except Exception as e:
        logger.error(f"Checkpoint okunamadı: {e}")
        return None
    
    if not snapshot or not snapshot.values:
        logger.info(f"Checkpoint yok: {project_id}")
        return None
    
    state = snapshot.values
    
    summary = {
        "project_id": state.get("project_id"),
        "sprint_id": state.get("sprint_id"),
        "approval_status": state.get("approval_status"),
        "file_stats": {
            "total": len(state.get("file_registry", {})),
            "done": sum(1 for s in state.get("file_registry", {}).values() if s == "done"),
            "failed": sum(1 for s in state.get("file_registry", {}).values() if s == "failed"),
        },
        "active_workers": len(state.get("active_workers", {})),
        "review_count": state.get("review_count", 0),
        "next_node": snapshot.next,
    }
    
    logger.debug(f"Checkpoint: {summary}")
    return summary

async def get_checkpoint_history(
    compiled_graph,
    project_id: str,
    limit: int = 5,
) -> list[dict]:
    config = get_thread_config(project_id)
    history = []
    
    async for snapshot in compiled_graph.aget_state_history(config=config):
        history.append({
            "ts": snapshot.created_at,
            "next": snapshot.next,
        })
        if len(history) >= limit:
            break
    
    return history
```

---

## References

- `graph-state-inspection-skill/SKILL.md` — state okuma
- `partial-sprint-recovery-skill/SKILL.md` — recovery
- `thread-config-usage-skill/SKILL.md` — thread config
