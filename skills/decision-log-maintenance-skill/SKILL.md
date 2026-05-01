---
name: decision-log-maintenance
description: Planner AI için — sprint boyunca alınan mimari ve teknik kararları Decision kaydı olarak DB'ye yazmak; ileride "neden böyle yaptık?" sorusunu yanıtlamak.
---

## Purpose

Önemli kararların neden alındığını kaydeder.
"Neden Telegram yerine CLI seçtik?" gibi soruları ileriki sprints için yanıtlar.
`decisions` tablosunda sprint başına kararlar saklanır.

---

## When to Apply

- Kullanıcı onay verirken (hangi plan onaylandı)
- Ret kararı alınırken (neden reddedildi)
- Mimari değişiklik yapılırken
- Alternatif yaklaşım seçilirken

---

## Rules

- Her onay bir `Decision` kaydı oluşturur.
- Her ret revizyon notu ile kaydedilir.
- Mimari değişiklik: "öncesi / sonrası" açıklamasıyla kaydedilir.
- `summary` kısa (1-2 cümle), `rationale` detaylı.
- Kararlar değiştirilemez (audit trail) — yeni karar eklenir.

---

## Guidelines

Decision kaydı oluşturma:
```python
# src/storage/models.py
class Decision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    sprint_id: str | None = None
    summary: str
    rationale: str
    decision_type: str = "general"  # "approval", "rejection", "architecture"
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Repository metodu
async def create_decision(self, decision: Decision) -> None:
    async with aiosqlite.connect(self.db_path) as conn:
        await conn.execute("""
            INSERT INTO decisions (decision_id, project_id, sprint_id, 
                                   summary, rationale, decision_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (decision.decision_id, decision.project_id, decision.sprint_id,
              decision.summary, decision.rationale, decision.decision_type,
              decision.created_at.isoformat()))
        await conn.commit()
```

PM'in karar kayıt örnekleri:
```python
# Onay kararı
await repo.create_decision(Decision(
    project_id=project_id,
    sprint_id=sprint_id,
    summary="Sprint 3 onaylandı: Telegram entegrasyonu",
    rationale=f"Kullanıcı onayladı: {approval_id}. "
              f"Plan: {plan_summary}",
    decision_type="approval"
))

# Ret kararı
await repo.create_decision(Decision(
    project_id=project_id,
    sprint_id=sprint_id,
    summary="Sprint 3 reddedildi",
    rationale=f"Kullanıcı gerekçesi: '{rejection_reason}'. "
              f"Revizyon: Kapsam daraltıldı.",
    decision_type="rejection"
))
```

---

## References

- `sprint-completion-validation-skill/SKILL.md` — sprint tamamlama
- `aiosqlite-patterns-skill/SKILL.md` — DB yazma
- `pm-mode-skill/SKILL.md` — onay workflow
