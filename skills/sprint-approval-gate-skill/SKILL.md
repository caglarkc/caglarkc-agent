---
name: sprint-approval-gate
description: Planner AI için — sprint başlamadan veya kritik bir adımda kullanıcı onayı beklemek; onay gelmezse harekete geçmemek.
---

## Purpose

Onaysız sprint başlatmak istenmeyen değişikliklere yol açar.
Onay kapısı: LangGraph `interrupt_before` ile akışı duraklatır.
Kullanıcı "evet" diyene kadar dispatcher tetiklenmez.

---

## When to Apply

- Sprint planı hazırlandıktan sonra onay beklenmesi gerektiğinde
- Kritik dosya (production config) değiştirilmeden önce
- Kullanıcı "her zaman onayıma sor" tercihini seçtiğinde

---

## Rules

- Onay kapısı: LangGraph `interrupt_before=["dispatcher"]` ile kurulur.
- Onay formu: görev listesi, tahmin süresi, etkilenen dosyalar.
- Timeout: 10 dakika — geçerse plan iptal edilir.
- Ret: kullanıcı "hayır" derse sprint `cancelled` olur.

---

## Guidelines

```python
from langgraph.types import interrupt

def approval_gate_node(state: dict) -> dict:
    """Kullanıcıdan onay bekleyen node."""
    plan_summary = build_plan_summary(state)
    
    # LangGraph interrupt — kullanıcı input bekle
    user_response = interrupt({
        "type":    "approval_request",
        "summary": plan_summary,
        "tasks":   state.get("tasks", []),
        "message": "Sprint planını onaylıyor musunuz? (evet/hayır)",
    })
    
    if str(user_response).lower().strip() in ("evet", "yes", "y", "e"):
        return {"sprint_approved": True, "sprint_status": "approved"}
    else:
        return {
            "sprint_approved": False,
            "sprint_status":   "cancelled",
            "cancellation_reason": "Kullanıcı onaylamadı",
        }

def build_plan_summary(state: dict) -> str:
    tasks = state.get("tasks", [])
    total_min = sum(t.get("estimated_minutes", 0) for t in tasks)
    files = list({f for t in tasks for f in t.get("files", [])})
    return (
        f"Görev sayısı: {len(tasks)}\n"
        f"Tahmini süre: {total_min} dakika\n"
        f"Etkilenen dosyalar: {', '.join(files[:5])}"
        + (f" ve {len(files)-5} daha" if len(files) > 5 else "")
    )
```

---

## References

- `approval-flow-orchestration-skill/SKILL.md` — onay akışı
- `approval-timeout-handling-skill/SKILL.md` — onay timeout
- `sprint-cancellation-skill/SKILL.md` — sprint iptal
