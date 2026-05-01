---
name: checkpoint-strategy-review
description: Planner AI için — LangGraph checkpoint konfigürasyonunun doğru yapılandırıldığını, state'in düzenli kaydedildiğini ve crash sonrası recovery'nin çalıştığını review sırasında doğrulamak.
---

## Purpose

Checkpoint mekanizmasının doğru kurulduğunu garantiler.
Daemon çöktüğünde state'in nereye kaydedildiğini ve nasıl geri yüklendiğini doğrular.
Thread ID yönetiminin tutarlı olduğunu kontrol eder.

---

## When to Apply

- `src/graph/graph.py` veya checkpoint ile ilgili kod review edilirken
- Recovery senaryosu test edilirken
- Yeni thread veya proje eklenirken

---

## Rules

- `AsyncSqliteSaver` kullanımı zorunlu — in-memory checkpointer production'da yasak.
- Thread ID: `{GRAPH_THREAD_PREFIX}_{project_id}` formatında.
- Her `graph.ainvoke()` çağrısında `configurable={"thread_id": thread_id}` geçilmeli.
- State snapshot (`state_snapshot_path`) ayrıca JSON'a yazılmalı.
- Recovery: daemon başlarken pending thread'ler tespit edilmeli ve resume edilmeli.
- Checkpoint DB ve state snapshot farklı konumlarda — ikisi de backup'lanmalı.

---

## Guidelines

Checkpoint konfigürasyon kontrol:
```python
# DOĞRU
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string(settings.graph_checkpoint_path) as checkpointer:
    graph = build_graph().compile(checkpointer=checkpointer)

# YANLIŞ — in-memory (crash sonrası kaybolur)
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()  # production'da yasak
```

Thread ID tutarlılığı:
```python
# Her çağrıda aynı thread_id kullanılmalı (aynı proje için)
thread_id = f"{settings.graph_thread_prefix}_{project_id}"
config = {"configurable": {"thread_id": thread_id}}

await graph.ainvoke(input_state, config=config)  # ilk çalıştırma
await graph.ainvoke(resume_input, config=config)  # resume — aynı thread_id
```

Recovery kontrol:
```python
# Daemon başlarken pending thread'ler tespit edilmeli
async def recover_pending_threads():
    snapshots = state_manager.get_all_projects()
    for project_id, project_state in snapshots.items():
        if project_state.get("status") == "pending":
            await graph_manager.resume_thread(project_id)
```

---

## References

- `langgraph-patterns-skill/SKILL.md` — checkpoint pattern'ları
- `partial-sprint-recovery-skill/SKILL.md` — recovery stratejisi
- `recovery-checkpoint-usage-skill/SKILL.md` — checkpoint kullanımı
