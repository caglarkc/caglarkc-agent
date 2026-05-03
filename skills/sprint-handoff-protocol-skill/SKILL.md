---
name: sprint-handoff-protocol
description: Planner AI için — bir sprint bittikten sonra sonraki sprinte veya başka bir sisteme kontrol devrederken gerekli bilgiyi aktarmak.
---

## Purpose

Sprint bitti — bir sonraki sprint sıfırdan başlamamalı.
Handoff protokolü: tamamlanan dosyalar, kararlar, açık sorunlar, öneriler.
Sonraki sprint veya sistem bu bilgiyle başlar.

---

## When to Apply

- Sprint tamamlandıktan sonra
- Farklı bir agent veya insan devralacaksa
- Çoklu sprint zincirinde bilgi aktarımı istendiğinde

---

## Rules

- Handoff belgesi: kısa (200 kelime), yapılandırılmış.
- İçerik: tamamlananlar, açık noktalar, öneriler, dikkat edilecekler.
- Format: markdown, hem insan hem makine okunabilir.
- Kayıt: sprint state'e eklenir, DB'ye yazılır.

---

## Guidelines

```python
def generate_handoff_document(state: dict) -> str:
    tasks      = state.get("tasks", [])
    done       = [t for t in tasks if t.get("status") == "done"]
    failed     = [t for t in tasks if t.get("status") == "failed"]
    notes      = state.get("sprint_notes", [])
    sprint_id  = state.get("sprint_id", "")

    open_issues = [
        n["content"] for n in notes if n.get("type") == "blocker"
    ]
    decisions = [
        n["content"] for n in notes if n.get("type") == "decision"
    ]

    sections = [
        f"# Handoff — {sprint_id}",
        "",
        "## Tamamlananlar",
        *[f"- ✓ `{t.get('file_path', t['id'])}`" for t in done[:10]],
        "",
    ]

    if failed:
        sections += [
            "## Tamamlanamayan Görevler",
            *[f"- ✗ {t.get('description', t['id'])}: {t.get('last_error', '?')[:60]}" for t in failed],
            "",
        ]

    if open_issues:
        sections += ["## Açık Sorunlar"]
        sections += [f"- {issue}" for issue in open_issues]
        sections.append("")

    if decisions:
        sections += ["## Alınan Kararlar"]
        sections += [f"- {d}" for d in decisions]
        sections.append("")

    sections += [
        "## Sonraki Sprint Önerisi",
        f"- Başarısız {len(failed)} görev retry edilebilir",
        f"- Backlog: {len(state.get('backlog', []))} öğe bekliyor",
    ]

    return "\n".join(sections)
```

---

## References

- `sprint-full-report-skill/SKILL.md` — tam rapor
- `multi-sprint-backlog-skill/SKILL.md` — çoklu sprint backlog
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
