---
name: sprint-velocity-tracking
description: Planner AI için — sprint hızını (velocity) ölçmek; her sprint kaç dosya/görev tamamladığını takip ederek ileriki sprints için gerçekçi tahmin yapmak.
---

## Purpose

"Bu sprint 5 dosya tamamladı, önceki 8 tamamlamıştı" — velocity düştü mü?
Velocity tracking, sprint kapasitesini gerçek veriyle belirlemeyi sağlar.
Aşırı iyimser planlama önlenir.

---

## When to Apply

- Sprint tamamlandıktan sonra otomatik velocity kaydedilirken
- Yeni sprint büyüklüğü planlanırken geçmiş hız baz alınırken
- Takım kapasitesi sorusu geldiğinde

---

## Rules

- Velocity: tamamlanan dosya sayısı / sprint süresi (saat).
- Son 5 sprint ortalaması = mevcut velocity.
- Velocity ani düşüşü (>%30): uyarı üretilir.
- Sprint bazlı saklanır: `sprint_metrics` tablosu.

---

## Guidelines

```python
from statistics import mean

async def get_velocity_stats(
    project_id: str,
    repo: ProjectRepository,
    last_n: int = 5,
) -> dict:
    sprints = await repo.list_sprints(
        project_id=project_id,
        status="done",
        limit=last_n,
        order_by="created_at DESC",
    )
    
    if not sprints:
        return {"avg_files": 0, "avg_tasks": 0, "trend": "unknown"}
    
    file_counts = []
    for s in sprints:
        done = sum(
            1 for status in (s.file_registry or {}).values()
            if status == "done"
        )
        file_counts.append(done)
    
    avg = mean(file_counts) if file_counts else 0
    
    # Trend: son sprint öncekilerden %30 düşük mü?
    trend = "stable"
    if len(file_counts) >= 2:
        recent = file_counts[0]
        historical_avg = mean(file_counts[1:])
        if historical_avg > 0 and recent < historical_avg * 0.7:
            trend = "declining"
        elif recent > historical_avg * 1.3:
            trend = "improving"
    
    return {
        "avg_files_per_sprint": round(avg, 1),
        "last_sprint_files": file_counts[0] if file_counts else 0,
        "trend": trend,
        "sample_size": len(file_counts),
    }
```

PM mesaj:
```
[PLANLAMA] Hız analizi:

Son 5 sprint ortalaması: 6.4 dosya/sprint
Son sprint: 5 dosya
Trend: Stabil

Bu sprint için önerilen boyut: 5-7 dosya
```

---

## References

- `sprint-metrics-collection-skill/SKILL.md` — metrikler
- `sprint-budget-estimation-skill/SKILL.md` — büyüklük tahmini
- `sprint-history-query-skill/SKILL.md` — geçmiş sorgu
