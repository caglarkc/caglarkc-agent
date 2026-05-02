---
name: state-initialization
description: Coder AI için — LangGraph graph'ı ilk başlatırken OrchestratorState'in zorunlu alanlarını doğru başlangıç değerleriyle hazırlamak.
---

## Purpose

State eksik alanlarla başlatılırsa ilk node hata verir.
Zorunlu alanların varsayılan değerleri belgelenmiş olmalı.
`ainvoke` çağrısına gönderilen initial state tam ve doğru olmalı.

---

## When to Apply

- Graph ilk kez çağrılırken (`ainvoke(initial_state, config)`)
- Yeni proje veya sprint başlatılırken
- `src/graph/state.py` veya `src/core/orchestrator.py` yazılırken

---

## Rules

- `project_id`: zorunlu — başlangıç state'inde olmalı.
- `messages`: liste başlangıcı — `[]` veya `[HumanMessage(...)]`.
- `file_registry`, `tasks`, `active_workers`: boş dict/liste.
- `approval_status`: `"pending"` (HITL bekleme).
- `review_count`: `0`.

---

## Guidelines

```python
from langchain_core.messages import HumanMessage

def build_initial_state(
    project_id: str,
    user_message: str,
) -> OrchestratorState:
    return {
        "project_id": project_id,
        "sprint_id": None,
        "messages": [HumanMessage(content=user_message)],
        "tasks": [],
        "file_registry": {},
        "active_workers": {},
        "dispatch_queue": [],
        "approval_status": "pending",
        "review_result": None,
        "review_comments": [],
        "review_count": 0,
        "sprint_summary": "",
        "validation_passed": False,
        "dispatch_complete": False,
    }

# Graph başlatma
async def start_sprint(
    compiled_graph,
    project_id: str,
    user_message: str,
) -> None:
    initial_state = build_initial_state(project_id, user_message)
    config = {"configurable": {"thread_id": project_id}}
    
    # Planner çalışır, dispatcher'da interrupt
    await compiled_graph.ainvoke(initial_state, config=config)
    logger.info(f"Sprint planlandı, onay bekleniyor: {project_id}")
```

Resume (HITL sonrası):
```python
async def resume_after_approval(compiled_graph, project_id: str) -> None:
    config = {"configurable": {"thread_id": project_id}}
    await compiled_graph.aupdate_state(
        config, {"approval_status": "approved"}
    )
    await compiled_graph.ainvoke(None, config=config)
```

---

## References

- `state-typeddict-definition-skill/SKILL.md` — state tanımı
- `graph-assembly-skill/SKILL.md` — graph derleme
- `interrupt-before-node-skill/SKILL.md` — HITL
