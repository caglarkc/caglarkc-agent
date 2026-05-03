---
name: state-migration
description: Coder AI için — OrchestratorState TypedDict'e yeni alan eklendiğinde mevcut checkpoint'lerdeki eski state'i uyumlu hale getirmek.
---

## Purpose

`OrchestratorState`'e yeni alan eklenirse eski checkpoint'ler bu alanı içermez.
Node yeni alanı varsayılan değerle bekler — eski state `KeyError` verir.
State migration eski checkpoint'leri yeni şemaya uyumlu yapar.

---

## When to Apply

- `OrchestratorState`'e zorunlu yeni alan eklendiğinde
- Checkpoint DB üzerinde çalışan sistemde şema değiştiğinde
- Daemon güncellendikten sonra ilk çalıştırmada

---

## Rules

- Yeni alan: `Optional` veya varsayılan değerle tanımlanır.
- Node'lar yeni alanı `.get("new_field", default)` ile okur.
- Migration: `aupdate_state` ile eksik alanı ekler.
- Otomatik migration: daemon başlarken çalışır.

---

## Guidelines

```python
# OrchestratorState'e yeni alan ekleme (geriye uyumlu)
class OrchestratorState(TypedDict, total=False):
    # Mevcut alanlar
    project_id: str
    sprint_id: str | None
    file_registry: dict[str, str]
    
    # Yeni eklenen alan — varsayılan ile
    sprint_paused: bool  # Varsayılan: False
    dead_letter_queue: list[dict]  # Varsayılan: []

# Node'da güvenli okuma
sprint_paused = state.get("sprint_paused", False)
dlq = state.get("dead_letter_queue", [])

# Startup migration
STATE_DEFAULTS = {
    "sprint_paused": False,
    "dead_letter_queue": [],
    "review_comments": [],
    "validation_passed": False,
}

async def migrate_checkpoint_state(
    compiled_graph,
    project_id: str,
) -> None:
    config = get_thread_config(project_id)
    snapshot = await compiled_graph.aget_state(config=config)
    
    if not snapshot or not snapshot.values:
        return
    
    current = snapshot.values
    needs_update = {
        key: default
        for key, default in STATE_DEFAULTS.items()
        if key not in current
    }
    
    if needs_update:
        await compiled_graph.aupdate_state(config=config, values=needs_update)
        logger.info(f"State migrated: {list(needs_update.keys())}")
```

---

## References

- `state-typeddict-definition-skill/SKILL.md` — state tanımı
- `graph-state-inspection-skill/SKILL.md` — state okuma
- `migration-strategy-skill/SKILL.md` — DB migration
