---
name: partial-sprint-recovery
description: Coder AI için — daemon restart sonrasında yarım kalan sprint'i checkpoint'ten okuyarak kaldığı yerden devam ettirme mantığını implemente etmek.
---

## Purpose

Daemon çöktüğünde tamamlanan dosya işleri kaybolmaz.
Recovery sonrasında sadece tamamlanmamış görevler yeniden çalışır.
`file_registry` durumuna göre hangi dosyaların yazılması gerektiği belirlenir.

---

## When to Apply

- `src/core/recovery.py` veya startup recovery kodu yazılırken
- Daemon başlarken pending thread tespiti yapılırken
- Graph resume mantığı implementasyonu gerektiğinde

---

## Rules

- Recovery sırasında `done` dosyalar tekrar yazılmaz.
- `in_progress` dosyalar `planned`'a geri alınır (worker yarıda kesmişti).
- `reserved` dosyalar `planned`'a geri alınır (dispatcher yarıda kesmişti).
- `failed` dosyalar retry sayısına göre yeniden planlanabilir.
- LangGraph checkpoint'ten resume ile idempotent çalışır.

---

## Guidelines

Recovery analizi:
```python
async def analyze_recovery(
    state: OrchestratorState
) -> RecoveryPlan:
    file_registry = state.get("file_registry", {})
    
    needs_retry = []
    already_done = []
    in_progress_reset = []
    
    for file_path, status in file_registry.items():
        if status == "done":
            already_done.append(file_path)
        elif status in ("in_progress", "reserved"):
            # Worker yarıda kesmişti → geri al
            in_progress_reset.append(file_path)
        elif status in ("planned", "failed"):
            needs_retry.append(file_path)
    
    return RecoveryPlan(
        skip=already_done,
        reset_to_planned=in_progress_reset,
        retry=needs_retry
    )


async def apply_recovery(
    compiled_graph,
    project_id: str,
    recovery_plan: RecoveryPlan
) -> None:
    config = get_thread_config(project_id)
    
    if recovery_plan.reset_to_planned:
        # in_progress/reserved → planned
        snapshot = await compiled_graph.aget_state(config=config)
        current_registry = snapshot.values.get("file_registry", {})
        
        updated_registry = {
            path: "planned" if status in ("in_progress", "reserved") else status
            for path, status in current_registry.items()
        }
        
        await compiled_graph.aupdate_state(
            config=config,
            values={"file_registry": updated_registry}
        )
    
    # Resume
    await compiled_graph.ainvoke(None, config=config)
    logger.info(f"Sprint recovery tamamlandı: {project_id}")
```

---

## References

- `checkpoint-strategy-review-skill/SKILL.md` — checkpoint
- `graph-state-inspection-skill/SKILL.md` — state okuma
- `idempotency-enforcement-skill/SKILL.md` — idempotent recovery
