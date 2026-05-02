---
name: state-persistence-recovery
description: Coder AI için — LangGraph state'ini kalıcı depolamaya yazmak ve çöküş sonrası geri yüklemek.
---

## Purpose

Sistem çöküşünde tüm sprint ilerlemesi kaybolabilir.
State persistence: her node çıkışında checkpoint kayıt altına alınır.
Recovery: en son checkpoint'ten kaldığı yerden devam eder.

---

## When to Apply

- LangGraph graph'ı compile edilirken checkpointer bağlanırken
- Çöküş sonrası sprint kurtarılırken
- Uzun süren sprint'lerde ilerleme korunurken

---

## Rules

- Checkpointer: `AsyncSqliteSaver` (production) veya `MemorySaver` (test).
- Thread ID: sprint_id kullanılır (her sprint ayrı thread).
- Recovery: `graph.aget_state(config)` ile son checkpoint okunur.
- Kısmi recovery: tamamlanan görevler tekrar çalıştırılmaz.

---

## Guidelines

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.memory import MemorySaver

async def create_checkpointer(db_path: str | None = None):
    if db_path:
        return AsyncSqliteSaver.from_conn_string(db_path)
    return MemorySaver()

def build_thread_config(sprint_id: str) -> dict:
    return {"configurable": {"thread_id": sprint_id}}

async def recover_sprint(
    graph,
    sprint_id: str,
) -> dict | None:
    config = build_thread_config(sprint_id)
    try:
        state = await graph.aget_state(config)
        if state and state.values:
            return state.values
    except Exception:
        pass
    return None

async def resume_sprint(
    graph,
    sprint_id: str,
    input_override: dict | None = None,
) -> None:
    config = build_thread_config(sprint_id)
    existing = await recover_sprint(graph, sprint_id)
    
    if not existing:
        raise ValueError(f"Sprint bulunamadı: {sprint_id}")
    
    # Kaldığı yerden devam et
    async for event in graph.astream(
        input_override or None,  # None = mevcut state'ten devam
        config=config,
    ):
        yield event

# Graph build
async def build_graph_with_persistence(db_path: str):
    from langgraph.graph import StateGraph
    checkpointer = await create_checkpointer(db_path)
    builder = StateGraph(OrchestratorState)
    # ... node'lar eklenir
    return builder.compile(checkpointer=checkpointer)
```

---

## References

- `checkpoint-inspection-skill/SKILL.md` — checkpoint inceleme
- `partial-sprint-recovery-skill/SKILL.md` — kısmi kurtarma
- `thread-config-usage-skill/SKILL.md` — thread konfigürasyonu
