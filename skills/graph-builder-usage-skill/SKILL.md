---
name: graph-builder-usage
description: Coder AI için — LangGraph StateGraph'ı doğru oluşturma, node ekleme, edge bağlama ve AsyncSqliteSaver ile compile etme.
---

## Purpose

`src/graph/graph.py`'deki `build_graph()` fonksiyonunu doğru şekilde günceller.
Yeni node veya edge eklenirken mevcut graph yapısıyla uyumlu kalınmasını sağlar.
Compile adımının checkpointer ile doğru yapılandırılmasını garantiler.

---

## When to Apply

- Yeni LangGraph node ekleneceğinde
- Graph akışına yeni edge veya dal eklenirken
- `build_graph()` fonksiyonu değiştirilirken

---

## Rules

- `StateGraph(OrchestratorState)` ile başlatılır.
- Her node `graph.add_node("name", node_function)` ile eklenir.
- Normal edge: `graph.add_edge("from", "to")`.
- Conditional edge: `graph.add_conditional_edges("from", routing_func, {...})`.
- Entry point: `graph.set_entry_point("planner")`.
- Compile: `graph.compile(checkpointer=checkpointer)` — checkpointer zorunlu.
- `AsyncSqliteSaver` ile compile — in-memory checkpointer yasak.

---

## Guidelines

build_graph() şablonu:
```python
from langgraph.graph import StateGraph
from langgraph.constants import END
from src.graph.state import OrchestratorState
from src.graph.edges import (
    route_after_planner,
    route_after_dispatcher,
    route_after_worker,
    route_after_validator,
    route_after_reviewer
)
from src.graph.nodes.planner import planner_node
from src.graph.nodes.dispatcher import dispatcher_node
from src.graph.nodes.worker import worker_node
from src.graph.nodes.executor import executor_node
from src.graph.nodes.validator import validator_node
from src.graph.nodes.reviewer import reviewer_node


def build_graph() -> StateGraph:
    graph = StateGraph(OrchestratorState)
    
    # Node'ları ekle
    graph.add_node("planner", planner_node)
    graph.add_node("dispatcher", dispatcher_node)
    graph.add_node("worker", worker_node)
    graph.add_node("executor", executor_node)
    graph.add_node("validator", validator_node)
    graph.add_node("reviewer", reviewer_node)
    
    # Entry point
    graph.set_entry_point("planner")
    
    # Conditional edge'ler
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {"dispatcher": "dispatcher", END: END}
    )
    graph.add_conditional_edges(
        "dispatcher",
        route_after_dispatcher,
        {"worker": "worker", "reviewer": "reviewer"}
    )
    
    # Normal edge'ler
    graph.add_edge("worker", "executor")
    graph.add_edge("executor", "validator")
    
    graph.add_conditional_edges(
        "validator",
        route_after_validator,
        {"reviewer": "reviewer", "dispatcher": "dispatcher"}
    )
    graph.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        {"dispatcher": "dispatcher", END: END}
    )
    
    return graph
```

Compile (graph_runtime context manager içinde):
```python
async with AsyncSqliteSaver.from_conn_string(settings.graph_checkpoint_path) as checkpointer:
    compiled = build_graph().compile(checkpointer=checkpointer)
    yield compiled
```

---

## References

- `conditional-edge-function-skill/SKILL.md` — edge fonksiyonları
- `checkpoint-strategy-review-skill/SKILL.md` — checkpointer
- `langgraph-patterns-skill/SKILL.md` — LangGraph referans
