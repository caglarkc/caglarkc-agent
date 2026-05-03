---
name: state-machine-design-review
description: Planner AI için — OrchestratorState, sprint lifecycle ve dosya status state machine'lerinin doğru tasarlandığını ve geçişlerin geçerli olduğunu review sırasında doğrulamak.
---

## Purpose

State geçişlerinin tutarlı ve eksiksiz olduğunu garantiler.
Geçersiz state geçişlerini (örn. "done" → "planned") yakalar.
State machine tasarımında eksik veya çakışan durumları tespit eder.

---

## When to Apply

- `src/graph/state.py` değişikliği review edilirken
- Yeni status enum değeri eklenirken
- Sprint veya dosya lifecycle'ı değiştirilirken
- Node'un state güncelleme mantığı kontrol edilirken

---

## Rules

- `FileStatus`: `planned → reserved → in_progress → done | failed` sırası korunur.
- `WorkerStatus`: `idle → reserved → working → idle` döngüsü korunur.
- Sprint status: `planned → running → completed | failed` sırası korunur.
- Geriye gidiş sadece explicit recovery durumunda (failed → planned retry).
- State mutasyonu yasak — node yeni dict döndürür.
- Orphan state (hiçbir zaman ulaşılamayan veya çıkılamayan) bırakılmaz.

---

## Guidelines

State geçiş tablosu review:
```
FileStatus geçiş kuralları:
planned   → reserved    (dispatcher atar, OK)
planned   → failed      (initialization error, OK)
reserved  → in_progress (worker başlar, OK)
reserved  → planned     (worker iptal, retry, OK)
in_progress → done      (worker tamamlar, OK)
in_progress → failed    (worker hata, OK)
done      → done        (idempotent, OK)
failed    → planned     (retry kararı, OK)

YASAK GEÇİŞLER:
done   → planned    (geri alınamaz)
done   → failed     (tamamlanmış iş bozulamaz)
```

Node state update kontrol:
```python
# DOĞRU — sadece değişen alanlar
async def planner_node(state: OrchestratorState) -> dict:
    return {
        "draft_plan": new_plan,
        "messages": state["messages"] + ["Plan oluşturuldu"]
    }

# YANLIŞ — tüm state döndürme
async def planner_node(state: OrchestratorState) -> OrchestratorState:
    state["draft_plan"] = new_plan  # mutasyon
    return state
```

---

## References

- `file-status-state-machine-skill/SKILL.md` — dosya state'leri
- `sprint-lifecycle-state-machine-skill/SKILL.md` — sprint state'leri
- `interface-contract-review-skill/SKILL.md` — kontrat doğrulama
