---
name: graph-invocation-async
description: Coder AI için — compile edilmiş LangGraph'ı ainvoke() ve astream() ile doğru çalıştırma; thread config, input state ve sonuç işleme.
---

## Purpose

Graph'ın doğru input ve config ile çalıştırılmasını sağlar.
Thread ID olmadan çalıştırılan graph checkpoint kaydedemez.
`ainvoke` vs `astream` seçimini netleştirir.

---

## When to Apply

- Graph ilk kez başlatılırken
- Kullanıcı yeni görev gönderdiğinde
- Onay alındıktan sonra graph resume edilirken

---

## Rules

- Her graph çağrısında `configurable={"thread_id": thread_id}` geçilmeli.
- Thread ID: `f"{settings.graph_thread_prefix}_{project_id}"` formatı.
- `ainvoke`: tüm execution tamamlanana kadar bekler, sonuç döner.
- `astream`: her adımı stream eder, event-driven kullanım için.
- Input: sadece ilk çalıştırmada `build_initial_state()` kullanılır.
- Resume: `None` veya delta input ile aynı thread_id ile çağrılır.

---

## Guidelines

İlk çalıştırma:
```python
from src.graph.state import build_initial_state

thread_id = f"{settings.graph_thread_prefix}_{project_id}"
config = {"configurable": {"thread_id": thread_id}}

initial_state = build_initial_state(
    project_id=project_id,
    task=task_description
)

# Tümünü çalıştır ve bekle
final_state = await compiled_graph.ainvoke(initial_state, config=config)
```

Onay sonrası resume:
```python
# Onay event'i alındıktan sonra
resume_input = {
    "approval_request": None,  # temizle
    "messages": [f"Plan onaylandı: {approval_id}"]
}
final_state = await compiled_graph.ainvoke(resume_input, config=config)
```

Stream ile adım adım izleme:
```python
async for chunk in compiled_graph.astream(initial_state, config=config):
    for node_name, node_output in chunk.items():
        logger.debug(f"Node {node_name} tamamlandı: {list(node_output.keys())}")
        await event_bus.emit("graph.node_completed", {
            "node": node_name,
            "project_id": project_id
        })
```

State inspection (interrupt sonrası):
```python
# Mevcut checkpoint state'ini oku
current_state = await compiled_graph.aget_state(config=config)
if current_state.next:
    logger.info(f"Sıradaki node: {current_state.next}")
```

---

## References

- `thread-config-management-skill/SKILL.md` — thread yönetimi
- `graph-state-inspection-skill/SKILL.md` — state okuma
- `checkpoint-strategy-review-skill/SKILL.md` — checkpointing
