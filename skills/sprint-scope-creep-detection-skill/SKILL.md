---
name: sprint-scope-creep-detection
description: Planner AI için — sprint sırasında kapsam genişlemesini (scope creep) tespit edip kullanıcıyı uyarmak.
---

## Purpose

Sprint başlarken 5 görev vardı, şimdi 15 var — kapsam kayması oldu.
Scope creep: planlanan görev sayısı veya dosya sayısı orijinalin %50'sini aşarsa.
Erken uyarı: sprint bitirilemeden kaynaklar tükenmez.

---

## When to Apply

- Görev listesine sprint sırasında yeni görev eklendiğinde
- Planlanan dosya sayısı önemli ölçüde artığında
- Sprint süresi başlangıç tahminini belirgin aşınca

---

## Rules

- Orijinal plan: sprint başlangıcında snapshot alınır.
- Eşik: %50 artış = uyarı; %100 artış = kullanıcı onayı gerekli.
- Scope creep bildirimi: ne kadar arttığı ve sebebi belirtilir.
- Onay gelmezse: eklenen görevler sonraki sprint'e ertelenir.

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class SprintScope:
    task_count:   int
    file_count:   int
    est_minutes:  int

def snapshot_scope(state: dict) -> SprintScope:
    tasks = state.get("tasks", [])
    files = {f for t in tasks for f in t.get("files", [])}
    total_min = sum(t.get("estimated_minutes", 0) for t in tasks)
    return SprintScope(len(tasks), len(files), total_min)

def detect_scope_creep(
    original: SprintScope,
    current: SprintScope,
) -> dict:
    task_growth = (current.task_count - original.task_count) / max(original.task_count, 1)
    file_growth = (current.file_count - original.file_count) / max(original.file_count, 1)
    
    status = "ok"
    if task_growth >= 1.0 or file_growth >= 1.0:
        status = "critical"
    elif task_growth >= 0.5 or file_growth >= 0.5:
        status = "warning"
    
    return {
        "status":       status,
        "task_growth":  f"+{task_growth*100:.0f}%",
        "file_growth":  f"+{file_growth*100:.0f}%",
        "original":     original,
        "current":      current,
    }

def format_scope_creep_message(report: dict) -> str:
    if report["status"] == "ok":
        return ""
    emoji = "⚠️" if report["status"] == "warning" else "🚨"
    return (
        f"{emoji} Kapsam kayması tespit edildi!\n"
        f"Görev artışı: {report['task_growth']}\n"
        f"Dosya artışı: {report['file_growth']}\n"
        f"Yeni görevler sonraki sprintte ele alınmalı."
    )
```

---

## References

- `sprint-scope-negotiation-skill/SKILL.md` — kapsam müzakeresi
- `sprint-budget-estimation-skill/SKILL.md` — bütçe tahmini
- `sprint-goal-validation-skill/SKILL.md` — hedef doğrulama
