---
name: interrupt-before-node
description: Coder AI için — LangGraph HITL (Human-in-the-Loop) interrupt pattern'ını uygulamak; belirli bir node'dan önce graph'ı durdurmak ve onay sonrası resume etmek.
---

## Purpose

Kullanıcı onayı gerektiren noktalarda graph'ı güvenle durdurur.
`interrupt_before=["node_name"]` ile compile zamanında interrupt noktası belirlenir.
Checkpoint sayesinde restart olmadan kaldığı yerden devam eder.

---

## When to Apply

- Plan onayı için planner → dispatcher geçişinde dur
- Büyük mimari değişiklik öncesinde dur
- Kullanıcı confirmation gerektiren kritik işlemlerde

---

## Rules

- Interrupt: `compile(checkpointer=..., interrupt_before=["dispatcher"])`.
- Graph interrupt olduğunda `snapshot.next == ("dispatcher",)` döner.
- Onay gelince: `aupdate_state()` ile state güncelle + `ainvoke(None, config)` ile resume.
- Interrupt sırasında state kaybolmaz — checkpoint'te saklanır.
- Timeout: ApprovalRequest 15 dakika sonra expire eder.

---

## Guidelines

Interrupt ile compile:
```python
compiled = build_graph().compile(
    checkpointer=checkpointer,
    interrupt_before=["dispatcher"]  # planner bittikten sonra dur
)
```

Interrupt tespiti:
```python
async def run_until_interrupt(self, project_id: str, initial_state: dict):
    config = get_thread_config(project_id)
    
    # Graph'ı çalıştır
    await compiled_graph.ainvoke(initial_state, config=config)
    
    # Nerede durdu?
    snapshot = await compiled_graph.aget_state(config=config)
    
    if snapshot.next == ("dispatcher",):
        # Interrupt: kullanıcı onayı bekleniyor
        approval_request = snapshot.values.get("approval_request")
        await event_bus.emit("plan.approval_needed", {
            "project_id": project_id,
            "approval_request": approval_request
        })
```

Resume (approval sonrası):
```python
async def on_plan_approved(self, project_id: str, approval_id: str):
    config = get_thread_config(project_id)
    
    # State'i güncelle
    await compiled_graph.aupdate_state(
        config=config,
        values={"approval_request": None}
    )
    
    # Kaldığı yerden devam et (None input = sadece state'i kullan)
    await compiled_graph.ainvoke(None, config=config)
    logger.info(f"Graph resume edildi: {project_id}")
```

---

## References

- `graph-state-inspection-skill/SKILL.md` — state okuma
- `approval-request-drafting-skill/SKILL.md` — onay formatı
- `graph-invocation-async-skill/SKILL.md` — graph çalıştırma
