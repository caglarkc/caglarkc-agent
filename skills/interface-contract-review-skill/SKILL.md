---
name: interface-contract-review
description: Planner AI için — fonksiyon imzaları, Pydantic modeller ve event kontratlarının doğru ve tutarlı olduğunu review sırasında doğrulamak.
---

## Purpose

Bileşenler arasındaki sözleşmelerin (kontratların) doğru tanımlandığını garantiler.
Bir fonksiyonun beklediği tip ile çağıranın verdiği tipin uyumluluğunu kontrol eder.
Kontrat değişikliğinin diğer bileşenleri kırmadığından emin olur.

---

## When to Apply

- Yeni Pydantic model veya TypedDict review edilirken
- Mevcut bir fonksiyon imzası değiştirilirken
- Event envelope yapısı değiştirilirken
- Node'un döndürdüğü dict kontrol edilirken

---

## Rules

- Node fonksiyonları: `async def node_name(state: OrchestratorState) -> dict` imzasını korur.
- Döndürülen dict sadece değişen state alanlarını içerir.
- Pydantic model alanları `Optional` değilse her zaman sağlanmalı.
- Event envelope: `event_type`, `payload`, `timestamp` zorunlu alanlar.
- ApprovalRequest: `approval_id`, `project_id`, `expires_at` zorunlu.
- Kontrat değişikliği = state.py veya contracts.py değişikliği = yeni onay gerektirir.

---

## Guidelines

Node imzası kontrol:
```python
# DOĞRU
async def planner_node(state: OrchestratorState) -> dict[str, Any]:
    return {"draft_plan": plan, "messages": [...]}

# YANLIŞ
async def planner_node(state: dict) -> OrchestratorState:  # tip yanlış
    state["draft_plan"] = plan  # mutasyon yasak, return edilmeli
    return state
```

Pydantic model kontrol:
```python
# DOĞRU
class FileRecord(BaseModel):
    file_id: str
    project_id: str
    path: str
    status: FileStatus  # enum, not str

# YANLIŞ
class FileRecord(BaseModel):
    file_id: str = ""  # boş default — zorunlu alan boş kalabilir
    status: str  # enum yerine str — tip güvencesi yok
```

Event kontrat kontrol:
```python
# Emit edilen event alıcıyla uyumlu mu?
emit("plan.generated", {"draft_plan": plan})  # payload key kontrol
# Subscriber:
def on_plan_generated(payload: dict):
    plan = payload["draft_plan"]  # key mevcut mu? ✓
```

---

## References

- `state-machine-design-review-skill/SKILL.md` — state kontratı
- `pydantic-v2-model-definition-skill/SKILL.md` — model tanımı
- `module-boundary-validation-skill/SKILL.md` — katman uyumu
