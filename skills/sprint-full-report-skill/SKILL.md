---
name: sprint-full-report
description: Planner AI için — sprint sonunda hedef, metrikler, dosyalar, notlar ve öğrenilen dersleri tek kapsamlı raporda birleştirmek.
---

## Purpose

Sprint bitti ama ne öğrendik, ne ürettik belgelenmiyor.
Tam rapor: KPI, audit log, sprint notes, diff raporu hepsini birleştirir.
Gelecek sprint planlaması ve ekip hafızası için temel kaynak.

---

## When to Apply

- Sprint tamamlandığında (reviewer node onayından sonra)
- Kullanıcı "tam rapor ver" dediğinde
- Haftalık retrospective dökümanı hazırlanırken

---

## Rules

- Rapor: hedef, süre, başarı oranı, üretilen dosyalar, kararlar, dersler.
- Uzunluk: 300-500 kelime.
- Format: markdown.
- Veriler: sprint_notes, sprint_kpi, file_registry'den beslenir.

---

## Guidelines

```python
from datetime import datetime

def generate_full_sprint_report(state: dict) -> str:
    sprint_id = state.get("sprint_id", "?")
    goal      = state.get("sprint_goal", "")
    tasks     = state.get("tasks", [])
    done      = [t for t in tasks if t.get("status") == "done"]
    failed    = [t for t in tasks if t.get("status") == "failed"]
    notes     = state.get("sprint_notes", [])
    started   = state.get("sprint_started_at", "")
    finished  = state.get("sprint_finished_at", datetime.utcnow().isoformat())

    mins = 0
    if started:
        s = datetime.fromisoformat(started)
        f = datetime.fromisoformat(finished)
        mins = int((f - s).total_seconds() / 60)

    files = list({f for t in done for f in t.get("files", []) if f})
    rate  = int(len(done) / len(tasks) * 100) if tasks else 0

    report = [
        f"# Sprint Tam Raporu — {sprint_id}",
        f"**Tarih**: {finished[:10]}  |  **Süre**: {mins} dk  |  **Başarı**: %{rate}",
        "",
        "## Hedef",
        goal, "",
        "## Görev Sonuçları",
        f"| Durum | Sayı |",
        f"|-------|------|",
        f"| Tamamlanan | {len(done)} |",
        f"| Başarısız  | {len(failed)} |",
        f"| Toplam     | {len(tasks)} |",
        "",
    ]

    if files:
        report += ["## Üretilen Dosyalar"]
        report += [f"- `{f}`" for f in files[:15]]
        if len(files) > 15:
            report.append(f"- ... ve {len(files)-15} dosya daha")
        report.append("")

    decisions = [n for n in notes if n.get("type") == "decision"]
    lessons   = [n for n in notes if n.get("type") == "lesson"]
    blockers  = [n for n in notes if n.get("type") == "blocker"]

    if decisions:
        report += ["## Alınan Kararlar"]
        report += [f"- {n['content']}" for n in decisions]
        report.append("")
    if blockers:
        report += ["## Karşılaşılan Sorunlar"]
        report += [f"- {n['content']}" for n in blockers]
        report.append("")
    if lessons:
        report += ["## Öğrenilen Dersler"]
        report += [f"- {n['content']}" for n in lessons]

    return "\n".join(report)
```

---

## References

- `sprint-kpi-dashboard-skill/SKILL.md` — KPI dashboard
- `sprint-note-taking-skill/SKILL.md` — sprint notları
- `sprint-diff-report-skill/SKILL.md` — değişim raporu
