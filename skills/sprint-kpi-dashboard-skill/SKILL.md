---
name: sprint-kpi-dashboard
description: Planner AI için — sprint performans göstergelerini (KPI) hesaplamak ve özet dashboard formatında sunmak.
---

## Purpose

Sprint bitti ama iyi mi gitti? Metriklere bakmadan bilinmez.
KPI dashboard: tamamlanma oranı, ortalama görev süresi, hata sayısı.
Sonraki sprint planlamasına veri sağlar.

---

## When to Apply

- Sprint tamamlandıktan sonra özet istendiğinde
- Kullanıcı "performans nasıl?" diye sorduğunda
- Sprint retrospective hazırlanırken

---

## Rules

- KPI'lar state'den hesaplanır, dış servis gerekmez.
- Gösterilecekler: tamamlanma %, ortalama süre, hata oranı, retry sayısı.
- Önceki sprint ile karşılaştırma (varsa).
- Çıktı: hem JSON (kayıt için) hem insan okunabilir metin.

---

## Guidelines

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SprintKPI:
    sprint_id: str
    total_tasks: int
    completed: int
    failed: int
    total_retries: int
    duration_minutes: float
    avg_task_minutes: float

def compute_sprint_kpi(state: dict) -> SprintKPI:
    tasks = state.get("tasks", [])
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == "done")
    failed    = sum(1 for t in tasks if t.get("status") == "failed")
    retries   = sum(t.get("retry_count", 0) for t in tasks)
    
    started_at  = state.get("sprint_started_at")
    finished_at = state.get("sprint_finished_at")
    duration = 0.0
    if started_at and finished_at:
        s = datetime.fromisoformat(started_at)
        f = datetime.fromisoformat(finished_at)
        duration = (f - s).total_seconds() / 60
    
    avg = duration / completed if completed else 0.0
    
    return SprintKPI(
        sprint_id=state.get("sprint_id", ""),
        total_tasks=total,
        completed=completed,
        failed=failed,
        total_retries=retries,
        duration_minutes=round(duration, 1),
        avg_task_minutes=round(avg, 1),
    )

def format_kpi_dashboard(kpi: SprintKPI) -> str:
    rate = (kpi.completed / kpi.total_tasks * 100) if kpi.total_tasks else 0
    return (
        f"Sprint KPI — {kpi.sprint_id}\n"
        f"  Tamamlanan : {kpi.completed}/{kpi.total_tasks} (%{rate:.0f})\n"
        f"  Başarısız  : {kpi.failed}\n"
        f"  Retry      : {kpi.total_retries}\n"
        f"  Süre       : {kpi.duration_minutes} dk\n"
        f"  Ort. görev : {kpi.avg_task_minutes} dk/görev"
    )
```

---

## References

- `sprint-metrics-collection-skill/SKILL.md` — metrik toplama
- `sprint-velocity-tracking-skill/SKILL.md` — velocity takibi
- `progress-report-generation-skill/SKILL.md` — ilerleme raporu
