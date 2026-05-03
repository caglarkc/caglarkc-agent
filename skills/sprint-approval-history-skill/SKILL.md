---
name: sprint-approval-history
description: Planner AI için — hangi sprint'lerin onaylandığını, reddedildiğini ve ne zaman onaylandığını sorgulamak; audit trail sağlamak.
---

## Purpose

"Bu sprint kim onayladı ne zaman?" sorusu cevaplanabilmeli.
Approval geçmişi Decision tablosundan sorgulanır.
Audit trail, hesap verebilirlik ve debugging için gereklidir.

---

## When to Apply

- Kullanıcı geçmiş sprint onaylarını sorduğunda
- Audit log sunulurken
- Sprint kararı tartışılırken kanıt gerektiğinde

---

## Rules

- Onay kararları `decision_type="approval"` ile kaydedilir.
- Ret kararları `decision_type="rejection"` ile.
- Geçmiş: son 10 karar yeterli.
- Sorgu: `project_id` ve opsiyonel `sprint_id` ile.

---

## Guidelines

```python
async def get_approval_history(
    project_id: str,
    repo: ProjectRepository,
    sprint_id: str | None = None,
    limit: int = 10,
) -> list[Decision]:
    decisions = await repo.list_decisions(
        project_id=project_id,
        decision_types=["approval", "rejection"],
        sprint_id=sprint_id,
        limit=limit,
        order_by="created_at DESC",
    )
    return decisions

def format_approval_history(decisions: list[Decision]) -> str:
    if not decisions:
        return "Henüz onay geçmişi yok."
    
    lines = ["Onay Geçmişi:"]
    for d in decisions:
        emoji = "✓" if d.decision_type == "approval" else "✗"
        date = d.created_at.strftime("%Y-%m-%d %H:%M")
        lines.append(f"  {emoji} [{date}] {d.summary}")
    
    return "\n".join(lines)
```

PM mesaj formatı:
```
[SOHBET] Sprint onay geçmişi:

  ✓ [2026-05-01 14:23] Sprint 3 onaylandı: LangGraph entegrasyonu
  ✗ [2026-04-30 10:15] Sprint 3 reddedildi: Kapsam çok geniş
  ✓ [2026-04-28 09:00] Sprint 2 onaylandı: Temel modeller
```

Repository metodu:
```python
async def list_decisions(
    self,
    project_id: str,
    decision_types: list[str] | None = None,
    sprint_id: str | None = None,
    limit: int = 10,
) -> list[Decision]:
    async with aiosqlite.connect(self.db_path) as conn:
        query = "SELECT * FROM decisions WHERE project_id = ?"
        params = [project_id]
        if sprint_id:
            query += " AND sprint_id = ?"
            params.append(sprint_id)
        if decision_types:
            placeholders = ",".join("?" * len(decision_types))
            query += f" AND decision_type IN ({placeholders})"
            params.extend(decision_types)
        query += f" ORDER BY created_at DESC LIMIT {limit}"
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return [Decision(**dict(row)) for row in rows]
```

---

## References

- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
- `sprint-history-query-skill/SKILL.md` — sprint geçmişi
- `aiosqlite-patterns-skill/SKILL.md` — DB sorgu
