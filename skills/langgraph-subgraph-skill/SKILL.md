---
name: langgraph-subgraph
description: Coder AI için — LangGraph içinde alt graf (subgraph) oluşturmak; karmaşık iş akışlarını izole modüller hâline getirmek.
---

## Purpose

Tek büyük graf yönetilemez hâle gelir.
Subgraph, bağımsız iş akışını kapsüller — kendi state'i, node'ları, edge'leri vardır.
Ana graf subgraph'ı tek node gibi çağırır.

---

## When to Apply

- Worker mantığı ana graftan bağımsız geliştirilirken
- Aynı alt akış birden fazla yerde kullanılırken
- Test için izole edilmesi gereken karmaşık akış varken

---

## Rules

- Subgraph kendi TypedDict state'ini tanımlar.
- Ana state ile subgraph state'i arasında veri dönüşümü açık yapılır.
- Subgraph ayrı compile edilir, ana grafa `add_node` ile eklenir.
- Subgraph checkpoint'i ana checkpoint'ten ayrı tutulabilir.

---

## Guidelines

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# Subgraph state
class WorkerSubState(TypedDict):
    file_path: str
    task: dict
    generated_code: str
    validation_result: str

def build_worker_subgraph():
    sg = StateGraph(WorkerSubState)
    
    sg.add_node("generate", generate_code_node)
    sg.add_node("validate", validate_code_node)
    sg.add_node("fix",      fix_code_node)
    
    sg.set_entry_point("generate")
    sg.add_edge("generate", "validate")
    sg.add_conditional_edges(
        "validate",
        lambda s: "fix" if s["validation_result"] == "failed" else END,
        {"fix": "fix", END: END},
    )
    sg.add_edge("fix", "validate")
    
    return sg.compile()

# Ana grafta subgraph kullanımı
def add_worker_subgraph(main_builder, worker_subgraph):
    def worker_adapter(main_state: dict) -> WorkerSubState:
        return {
            "file_path": main_state["current_file"],
            "task":      main_state["current_task"],
            "generated_code": "",
            "validation_result": "",
        }
    
    def merge_worker_result(main_state: dict, sub_result: WorkerSubState) -> dict:
        return {
            "generated_files": {
                **main_state.get("generated_files", {}),
                sub_result["file_path"]: sub_result["generated_code"],
            }
        }
    
    main_builder.add_node(
        "worker",
        lambda s: merge_worker_result(s, worker_subgraph.invoke(worker_adapter(s))),
    )
```

---

## References

- `graph-assembly-skill/SKILL.md` — ana graf kurulumu
- `worker-node-implementation-skill/SKILL.md` — worker node
- `thread-config-usage-skill/SKILL.md` — thread konfigürasyonu
