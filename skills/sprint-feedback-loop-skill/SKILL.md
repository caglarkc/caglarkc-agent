---
name: sprint-feedback-loop
description: Planner AI için — sprint sonuçlarından öğrenerek bir sonraki sprint planlamasını iyileştirmek.
---

## Purpose

Her sprint bağımsız planlanır — önceki hatalardan öğrenilmez.
Feedback loop: hata oranı, ortalama süre, en çok retry alan görev türleri analiz edilir.
Bir sonraki sprint: bu verilerle daha gerçekçi tahminler yapar.

---

## When to Apply

- Sprint tamamlandıktan sonra analiz yapılırken
- Tekrar eden hata türleri tespit edildiğinde
- Sonraki sprint tahmini kalibrasyonu gerektiğinde

---

## Rules

- Feedback: en az 3 sprint verisi gerekir (1-2 ile anlamlı değil).
- Analiz: görev türü bazında başarı oranı, ortalama süre.
- Sonuç: bir sonraki benzer göreve eklenen tahmin çarpanı.
- Feedback kaydı: sprint_feedback tablosunda saklanır.

---

## Guidelines

```python
from statistics import mean, stdev
from collections import defaultdict

def analyze_sprint_history(sprints: list[dict]) -> dict:
    if len(sprints) < 3:
        return {}
    
    task_type_stats: dict[str, list] = defaultdict(list)
    
    for sprint in sprints:
        for task in sprint.get("tasks", []):
            task_type = task.get("type", "generic")
            actual = task.get("actual_minutes", task.get("estimated_minutes", 0))
            estimated = task.get("estimated_minutes", 0)
            success = task.get("status") == "done"
            
            task_type_stats[task_type].append({
                "ratio":   actual / estimated if estimated else 1.0,
                "success": success,
            })
    
    result = {}
    for task_type, records in task_type_stats.items():
        ratios  = [r["ratio"]   for r in records]
        success = [r["success"] for r in records]
        result[task_type] = {
            "avg_time_ratio":   round(mean(ratios), 2),
            "success_rate":     round(mean(success) * 100, 1),
            "sample_count":     len(records),
            "recommended_multiplier": round(mean(ratios) * 1.1, 2),
        }
    return result

def apply_feedback_to_task(task: dict, feedback: dict) -> dict:
    task_type = task.get("type", "generic")
    stats = feedback.get(task_type, {})
    multiplier = stats.get("recommended_multiplier", 1.0)
    
    adjusted = dict(task)
    adjusted["estimated_minutes"] = int(
        task.get("estimated_minutes", 20) * multiplier
    )
    adjusted["adjusted_by_feedback"] = True
    return adjusted
```

---

## References

- `sprint-velocity-tracking-skill/SKILL.md` — velocity takibi
- `task-estimation-calibration-skill/SKILL.md` — tahmin kalibrasyonu
- `sprint-kpi-dashboard-skill/SKILL.md` — KPI dashboard
