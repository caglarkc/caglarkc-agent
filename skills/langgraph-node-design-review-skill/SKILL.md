---
name: langgraph-node-design-review
description: Planner AI için — LangGraph node implementasyonlarının doğru sorumluluk ayrımına sahip olduğunu, state güncelleme pattern'larına uyduğunu ve graph akışıyla uyumlu çalıştığını review sırasında doğrulamak.
---

## Purpose

Her node'un tek bir sorumlulukla tasarlandığını garantiler.
Node'un state'i doğru okuduğunu ve sadece değişen alanları döndürdüğünü kontrol eder.
Node içinde routing mantığı olmadığını (bu edges.py'nin işi) doğrular.

---

## When to Apply

- `src/graph/nodes/*.py` review edilirken
- Yeni node implementasyonu geldiğinde
- Mevcut node'a yeni sorumluluk eklenmesi istendiğinde

---

## Rules

- Her node: `async def <name>_node(state: OrchestratorState) -> dict`
- Node sadece kendi sorumluluğundaki state alanlarını yazar.
- Routing (if/else ile başka node'a yönlendirme) node içinde olmaz → `edges.py`.
- Node başka node'u direkt çağırmaz.
- Node dış servislerle iletişim kurar ama interface'e bağımlı olmaz.
- Her node event emit edebilir (event bus üzerinden).
- Node'da `while` döngüsü veya uzun sleep yasak.

---

## Guidelines

Node sorumluluk haritası:
```
planner.py  → LLM ile plan üretimi, draft_plan ve worker_queue güncelleme
dispatcher.py → Görev atama, worker_status ve worker_queue güncelleme
worker.py   → Dosya üretimi, file_registry ve FileRecord güncelleme
executor.py → Statik analiz, validation_issues güncelleme
validator.py → Doğrulama mantığı, validation_issues okuma
reviewer.py → Review kararı, sprint status güncelleme
```

Node tasarım kontrol:
```python
# DOĞRU
async def planner_node(state: OrchestratorState) -> dict:
    plan = await manager_service.process_turn(
        state["task_description"],
        state["conversation_history"]
    )
    return {
        "draft_plan": plan.draft_plan,
        "messages": state["messages"] + ["Plan üretildi"],
        "approval_request": build_approval_request(plan)
    }

# YANLIŞ — routing node içinde
async def planner_node(state: OrchestratorState) -> str:
    if needs_approval:
        return "END"  # Bu edges.py'de olmalı
    return "dispatcher"
```

---

## References

- `langgraph-patterns-skill/SKILL.md` — LangGraph kuralları
- `langgraph-edge-routing-review-skill/SKILL.md` — edge routing
- `state-machine-design-review-skill/SKILL.md` — state yönetimi
