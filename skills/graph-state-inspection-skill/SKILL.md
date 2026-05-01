---
name: graph-state-inspection
description: Coder AI için — çalışan veya durdurulmuş bir LangGraph thread'inin mevcut state'ini okumak, sıradaki node'u öğrenmek ve state'i manuel güncellemek.
---

## Purpose

Graph'ın nerede durduğunu ve ne beklediğini programatik olarak sorgulamayı sağlar.
`aget_state()` ile checkpoint'ten mevcut state okunur.
`aupdate_state()` ile HITL approval sırasında state manuel güncellenir.

---

## When to Apply

- Daemon startup'ta pending thread'leri tespit ederken
- HITL interrupt sonrası onay verilirken
- Debug veya monitoring amacıyla state okunurken
- `system.stalled` sonrası durumu kontrol ederken

---

## Rules

- `aget_state(config)` her zaman config ile çağrılır.
- `state_snapshot.next` → sıradaki node listesi (boşsa graph bitti).
- `state_snapshot.values` → mevcut OrchestratorState.
- `aupdate_state()` ile state güncellemesi dikkatli yapılır — checkpoint'i değiştirir.
- Okuma `aget_state()`, güncelleme `aupdate_state()` ayrı operasyonlardır.

---

## Guidelines

State okuma:
```python
config = get_thread_config(project_id)

# Mevcut state
snapshot = await compiled_graph.aget_state(config=config)

current_values = snapshot.values  # OrchestratorState dict
next_nodes = snapshot.next  # tuple of node names
metadata = snapshot.metadata  # step, source bilgisi

if not next_nodes:
    logger.info(f"Graph tamamlandı: {project_id}")
elif "planner" in next_nodes:
    logger.info(f"Planner bekliyor (interrupt): {project_id}")
```

State history:
```python
# Tüm checkpoint geçmişi
async for state in compiled_graph.aget_state_history(config=config):
    logger.debug(f"Step {state.metadata.get('step')}: {state.next}")
```

Manuel state güncelleme (approval için):
```python
async def approve_plan(self, project_id: str, approval_id: str):
    config = get_thread_config(project_id)
    
    # Approval'ı state'e yaz
    await compiled_graph.aupdate_state(
        config=config,
        values={
            "approval_request": None,  # temizle
            "messages": ["Plan onaylandı"]
        }
    )
    
    # Graph'ı resume et
    await compiled_graph.ainvoke(None, config=config)
```

---

## References

- `graph-invocation-async-skill/SKILL.md` — graph çalıştırma
- `thread-config-management-skill/SKILL.md` — thread yönetimi
- `interrupt-before-node-skill/SKILL.md` — HITL interrupt
