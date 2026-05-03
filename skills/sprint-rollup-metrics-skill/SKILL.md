---
name: sprint-rollup-metrics
description: Planner AI için — birden fazla sprintin metriklerini toplayarak proje düzeyinde istatistik üretmek.
---

## Purpose

Tek sprint metrikleri anlık görünüm verir.
Rollup: haftalık/aylık bazda toplam başarı oranı, ortalama süre, trend.
"Sistem zamanla daha iyi mi oluyor?" sorusunu yanıtlar.

---

## When to Apply

- Birden fazla sprint tamamlandığında proje özetleri istendiğinde
- Haftalık veya aylık rapor hazırlanırken
- Sistem performansı değerlendirilirken

---

## Rules

- Rollup: en az 3 sprint verisi gerekir.
- Metrikler: ortalama tamamlanma oranı, retry azalması, süre trendi.
- Trend: artış/azalış yönü (↑↓→).
- Çıktı: JSON + insan okunabilir özet.

---

## Guidelines

```python
from statistics import mean, stdev
from datetime import datetime

def compute_rollup_metrics(sprints: list[dict]) -> dict:
    if len(sprints) < 2:
        return {"error": "En az 2 sprint gerekli"}

    completion_rates = []
    durations        = []
    retry_counts     = []

    for s in sprints:
        tasks = s.get("tasks", [])
        total = len(tasks)
        if total == 0:
            continue
        done = sum(1 for t in tasks if t.get("status") == "done")
        completion_rates.append(done / total)
        retry_counts.append(sum(t.get("retry_count", 0) for t in tasks))

        started  = s.get("sprint_started_at")
        finished = s.get("sprint_finished_at")
        if started and finished:
            d = (datetime.fromisoformat(finished) - datetime.fromisoformat(started)).total_seconds() / 60
            durations.append(d)

    def trend(values: list[float]) -> str:
        if len(values) < 2:
            return "→"
        delta = values[-1] - values[0]
        return "↑" if delta > 0.05 else ("↓" if delta < -0.05 else "→")

    return {
        "sprint_count":    len(sprints),
        "avg_completion":  round(mean(completion_rates) * 100, 1) if completion_rates else 0,
        "avg_duration":    round(mean(durations), 1) if durations else 0,
        "avg_retries":     round(mean(retry_counts), 1) if retry_counts else 0,
        "completion_trend": trend(completion_rates),
        "duration_trend":   trend(durations),
        "retry_trend":      trend(retry_counts),
    }

def format_rollup(metrics: dict) -> str:
    return (
        f"Proje Metrikleri ({metrics['sprint_count']} sprint):\n"
        f"  Tamamlanma: %{metrics['avg_completion']} {metrics['completion_trend']}\n"
        f"  Ort. süre  : {metrics['avg_duration']} dk {metrics['duration_trend']}\n"
        f"  Ort. retry : {metrics['avg_retries']} {metrics['retry_trend']}"
    )
```

---

## References

- `sprint-kpi-dashboard-skill/SKILL.md` — KPI dashboard
- `sprint-velocity-tracking-skill/SKILL.md` — velocity takibi
- `sprint-feedback-loop-skill/SKILL.md` — geri besleme döngüsü
