---
name: sprint-capacity-planning
description: Planner AI için — mevcut kaynakları (worker sayısı, LLM kapasitesi) göz önünde bulundurarak sprint hacmini belirlemek.
---

## Purpose

4 worker var ama 40 görev planlandı — gerçekçi değil.
Capacity planning: worker başına kaç görev, toplam ne kadar iş sığar?
Aşırı yükleme önlenir, sprint tahminleri güvenilir olur.

---

## When to Apply

- Sprint planı oluşturulurken kapasite hesabı yapılırken
- Mevcut system config'den worker sayısı alınırken
- "Bu sprint'e ne kadar sığar?" sorusu yanıtlanırken

---

## Rules

- Kapasite = `MAX_WORKERS × ortalama_görev_süresi × sprint_süresi`.
- %80 kapasite ile plan yapılır — %20 buffer.
- Aşım: düşük öncelikli görevler backlog'a eklenir.
- Kapasite raporu kullanıcıya onay ekranında gösterilir.

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class CapacityPlan:
    max_workers:      int
    sprint_minutes:   float
    avg_task_minutes: float
    buffer_pct:       float = 0.20
    
    @property
    def total_capacity_minutes(self) -> float:
        return self.max_workers * self.sprint_minutes * (1 - self.buffer_pct)
    
    @property
    def max_tasks(self) -> int:
        if self.avg_task_minutes <= 0:
            return 0
        return int(self.total_capacity_minutes / self.avg_task_minutes)

def check_sprint_capacity(
    tasks: list[dict],
    plan: CapacityPlan,
) -> dict:
    total_min  = sum(t.get("estimated_minutes", 20) for t in tasks)
    fits_count = 0
    overflow   = []
    cumulative = 0.0
    
    for task in sorted(tasks, key=lambda t: t.get("priority", 3)):
        est = task.get("estimated_minutes", 20)
        if cumulative + est <= plan.total_capacity_minutes:
            cumulative += est
            fits_count += 1
        else:
            overflow.append(task)
    
    return {
        "fits_in_sprint":     fits_count,
        "overflow_count":     len(overflow),
        "overflow_tasks":     [t["id"] for t in overflow],
        "utilization_pct":    round(cumulative / plan.total_capacity_minutes * 100, 1),
        "total_minutes_est":  total_min,
        "capacity_minutes":   plan.total_capacity_minutes,
    }

def format_capacity_report(result: dict) -> str:
    return (
        f"Kapasite Planı:\n"
        f"  Sprint'e sığan: {result['fits_in_sprint']} görev\n"
        f"  Ertelenen    : {result['overflow_count']} görev\n"
        f"  Kullanım     : %{result['utilization_pct']}\n"
        f"  Tahmini süre : {result['total_minutes_est']} dk"
    )
```

---

## References

- `sprint-budget-estimation-skill/SKILL.md` — bütçe tahmini
- `worker-assignment-strategy-skill/SKILL.md` — worker atama stratejisi
- `sprint-scope-creep-detection-skill/SKILL.md` — kapsam kayması tespiti
