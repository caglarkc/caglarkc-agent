---
name: graph-assembly
description: Coder AI için — LangGraph StateGraph'ını tüm node'lar ve edge'lerle birleştirerek derlenmiş graph oluşturmak.
---

## Purpose

Her node ayrı ayrı implemente edilir; graph assembly bunları bağlar.
Yanlış edge tanımı akışı kırar — assembly aşamasında yakalanır.
`compile()` ile checkpointer ve interrupt_before bağlanır.

---

## When to Apply

- `src/graph/builder.py` yazılırken
- Yeni node eklendikten sonra graph'a bağlanırken
- Checkpointer ve HITL konfigürasyonu yapılırken

---

## Rules

- Her node `builder.add_node()` ile eklenir.
- `START` → ilk node, son node → `END` ile bağlanır.
- Conditional edge: `add_conditional_edges()` ile.
- `interrupt_before=["dispatcher"]`: HITL gate.
- `compile()` en son çağrılır.

---

## Guidelines

```python
# src/graph/builder.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver

def build_graph(
    repo: ProjectRepository,
    llm: BaseChatModel,
    checkpoint_path: str,
    event_bus: EventBus,
) -> StateGraph:
    builder = StateGraph(OrchestratorState)
    
    # Node'ları ekle
    builder.add_node("planner",    make_planner_node(repo, llm))
    builder.add_node("dispatcher", make_dispatcher_node(repo))
    builder.add_node("executor",   make_executor_node(llm))
    builder.add_node("validator",  validator_node)
    builder.add_node("reviewer",   make_reviewer_node(llm))
    
    # Edge'leri tanımla
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "dispatcher")
    builder.add_edge("dispatcher", "executor")
    builder.add_edge("executor", "validator")
    
    # Conditional edge: validator sonrası
    builder.add_conditional_edges(
        "validator",
        route_after_validation,
        {"reviewer": "reviewer", "executor": "executor"},
    )
    builder.add_conditional_edges(
        "reviewer",
        route_after_review,
        {"done": END, "worker": "executor"},
    )
    
    return builder

def compile_graph(
    builder: StateGraph,
    checkpoint_path: str,
) -> CompiledGraph:
    checkpointer = AsyncSqliteSaver.from_conn_string(checkpoint_path)
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["dispatcher"],
    )
```

---

## References

- `graph-builder-usage-skill/SKILL.md` — builder API
- `interrupt-before-node-skill/SKILL.md` — HITL
- `checkpoint-strategy-review-skill/SKILL.md` — checkpoint
