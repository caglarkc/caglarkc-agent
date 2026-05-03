---
name: sprint-lifecycle-state-machine
description: Planner AI için — bir sprint'in tüm yaşam döngüsü durumlarını (draft → active → review → done/cancelled) yönetmek; geçersiz geçişleri engellemek.
---

## Purpose

Sprint durumu rastgele değiştirilirse sistem tutarsız olur.
State machine, hangi geçişin ne zaman geçerli olduğunu zorlar.
`done` sprint tekrar `active` yapılamaz.

---

## When to Apply

- Sprint oluşturma, onaylama, tamamlama, iptal etme kodu yazılırken
- Sprint tablosuna `status` alanı eklenirken
- PM node'da sprint geçiş mantığı implemente edilirken

---

## Rules

- Sadece tanımlı geçişler geçerlidir — geçersiz geçiş `InvalidStateTransition` fırlatır.
- `cancelled` ve `done` terminal durumlar — üzerinden geçiş yapılamaz.
- Geçiş anında timestamp kaydedilir (`transitioned_at`).
- Her geçiş log'a yazılır.

---

## Guidelines

```python
from enum import Enum

class SprintStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"

# Geçerli geçişler
VALID_TRANSITIONS: dict[SprintStatus, set[SprintStatus]] = {
    SprintStatus.DRAFT:      {SprintStatus.ACTIVE, SprintStatus.CANCELLED},
    SprintStatus.ACTIVE:     {SprintStatus.REVIEW, SprintStatus.CANCELLED},
    SprintStatus.REVIEW:     {SprintStatus.DONE, SprintStatus.ACTIVE},
    SprintStatus.DONE:       set(),   # terminal
    SprintStatus.CANCELLED:  set(),   # terminal
}

class InvalidStateTransition(Exception):
    pass

def transition_sprint(
    current: SprintStatus,
    target: SprintStatus
) -> SprintStatus:
    if target not in VALID_TRANSITIONS[current]:
        raise InvalidStateTransition(
            f"Geçersiz geçiş: {current} → {target}. "
            f"İzin verilenler: {VALID_TRANSITIONS[current]}"
        )
    logger.info(f"Sprint durumu güncellendi: {current} → {target}")
    return target
```

DB güncelleme:
```python
async def update_sprint_status(
    sprint_id: str,
    new_status: SprintStatus,
    conn: aiosqlite.Connection
) -> None:
    await conn.execute(
        "UPDATE sprints SET status=?, updated_at=? WHERE sprint_id=?",
        (new_status.value, datetime.utcnow().isoformat(), sprint_id)
    )
    await conn.commit()
```

---

## References

- `file-status-state-machine-skill/SKILL.md` — dosya durumu
- `sprint-completion-validation-skill/SKILL.md` — tamamlanma
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
