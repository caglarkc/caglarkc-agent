---
name: sprint-stakeholder-update
description: Planner AI için — sprint ilerlemesini paydaşlara (kullanıcıya) anlaşılır dilde düzenli raporlamak.
---

## Purpose

Teknik sprint durumu kullanıcıya ham formda sunulursa anlaşılmaz.
Paydaş güncellemesi: teknik detayları gizler, ilerlemeyi basit dille anlatır.
"X tamamlandı, Y devam ediyor, Z engellenmiş" formatı yeterlidir.

---

## When to Apply

- Sprint ilerleme bildirimi gönderilirken
- Kullanıcı "durum nedir?" diye sorduğunda
- Uzun süren sprint'te periyodik güncelleme yapılırken

---

## Rules

- Güncelleme sıklığı: her %25 ilerlemede veya her 15 dakikada bir.
- Format: tamamlanan, devam eden, engellenmiş.
- Teknik jargon yok — dosya isimleri yerine özellik isimleri.
- Tahmini bitiş süresi varsa dahil edilir.

---

## Guidelines

```python
def build_stakeholder_update(state: dict) -> str:
    tasks = state.get("tasks", [])
    done       = [t for t in tasks if t.get("status") == "done"]
    in_prog    = [t for t in tasks if t.get("status") == "in_progress"]
    blocked    = [t for t in tasks if t.get("status") == "failed"]
    pending    = [t for t in tasks if t.get("status") == "planned"]
    
    total = len(tasks)
    pct   = int(len(done) / total * 100) if total else 0
    
    lines = [
        f"Sprint İlerlemesi: %{pct} ({len(done)}/{total} görev)",
        "",
    ]
    
    if done:
        lines.append("Tamamlanan:")
        for t in done[-3:]:  # Son 3 tane
            lines.append(f"  ✓ {t.get('description', t.get('id', ''))[:60]}")
    
    if in_prog:
        lines.append("\nDevam Eden:")
        for t in in_prog:
            lines.append(f"  ⟳ {t.get('description', t.get('id', ''))[:60]}")
    
    if blocked:
        lines.append("\nEngellenmiş:")
        for t in blocked:
            reason = t.get("error", "Bilinmiyor")[:40]
            lines.append(f"  ✗ {t.get('description', '')[:40]} ({reason})")
    
    if pending:
        lines.append(f"\nBekleyen: {len(pending)} görev")
    
    eta = state.get("estimated_finish_at")
    if eta:
        lines.append(f"\nTahmini bitiş: {eta[:16]}")
    
    return "\n".join(lines)
```

---

## References

- `progress-report-generation-skill/SKILL.md` — ilerleme raporu
- `sprint-kpi-dashboard-skill/SKILL.md` — KPI dashboard
- `user-feedback-collection-skill/SKILL.md` — kullanıcı geri bildirimi
