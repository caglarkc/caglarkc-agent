---
name: sprint-release-notes
description: Planner AI için — tamamlanan sprint'ten kullanıcıya sunmak üzere sürüm notları oluşturmak.
---

## Purpose

Sprint bitti ama "ne yaptık, kullanıcıya nasıl anlatalım?" sorusu yanıtsız.
Release notes: teknik değişiklikleri insan dostu dile çevirir.
Git commit'leri ve görev açıklamalarından otomatik üretilir.

---

## When to Apply

- Sprint tamamlandığında son kullanıcı bildirimi hazırlanırken
- Versiyon çıkarılmadan önce değişiklik listesi oluşturulurken
- Kullanıcı "ne değişti?" diye sorduğunda

---

## Rules

- Format: Türkçe, kısa madde listesi, teknik jargon yok.
- Kategoriler: Yeni Özellikler, İyileştirmeler, Düzeltmeler.
- Tamamlanmamış görevler dahil edilmez.
- Versiyon numarası: `MAJOR.MINOR.PATCH` (sprint sonrası minor artar).

---

## Guidelines

```python
from datetime import datetime

def generate_release_notes(
    state: dict,
    version: str | None = None,
) -> str:
    tasks    = state.get("tasks", [])
    done     = [t for t in tasks if t.get("status") == "done"]
    
    new_features   = [t for t in done if t.get("type") == "feature"]
    improvements   = [t for t in done if t.get("type") == "improvement"]
    fixes          = [t for t in done if t.get("type") == "fix"]
    other          = [t for t in done if t.get("type") not in ("feature", "improvement", "fix")]
    
    ver = version or _auto_version(state)
    date = datetime.utcnow().strftime("%Y-%m-%d")
    
    lines = [f"## Sürüm {ver} — {date}", ""]
    
    if new_features:
        lines.append("### Yeni Özellikler")
        for t in new_features:
            lines.append(f"- {t.get('description', t['id'])}")
        lines.append("")
    
    if improvements:
        lines.append("### İyileştirmeler")
        for t in improvements:
            lines.append(f"- {t.get('description', t['id'])}")
        lines.append("")
    
    if fixes:
        lines.append("### Düzeltmeler")
        for t in fixes:
            lines.append(f"- {t.get('description', t['id'])}")
        lines.append("")
    
    if other:
        lines.append("### Diğer")
        for t in other:
            lines.append(f"- {t.get('description', t['id'])}")
    
    return "\n".join(lines)

def _auto_version(state: dict) -> str:
    sprint_count = state.get("completed_sprint_count", 1)
    return f"0.{sprint_count}.0"
```

---

## References

- `sprint-diff-report-skill/SKILL.md` — sprint diff raporu
- `sprint-completion-celebration-skill/SKILL.md` — tamamlanma bildirimi
- `sprint-export-skill/SKILL.md` — sprint dışa aktarma
