---
name: sprint-milestone-tracking
description: Planner AI için — sprint içinde kritik dönüm noktalarını (milestone) tanımlamak ve ulaşıldığında bildirmek.
---

## Purpose

Uzun sprint'te "ne zaman bitecek?" sorusu belirsiz kalır.
Milestone'lar: %25, %50, %75 gibi ara hedefler veya kritik dosya tamamlanmaları.
Her milestone'da kullanıcı bilgilendirilir, motivasyon artar.

---

## When to Apply

- 10+ görevlik sprint planlanırken
- Kullanıcı ara durum bildirimi istediğinde
- Sprint planında kritik bağımlılıklar varken

---

## Rules

- Milestone en az 3, en fazla 5 adet.
- Otomatik milestone: %25, %50, %75, %100.
- Özel milestone: kritik görev tamamlanınca (örn. "veritabanı şeması hazır").
- Geçilen milestone: state'e kaydedilir, tekrar bildirilmez.

---

## Guidelines

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Milestone:
    name: str
    trigger: str  # "percent:50" | "task:db_schema"
    reached_at: str | None = None

def define_milestones(tasks: list[dict]) -> list[Milestone]:
    milestones = [
        Milestone("Çeyrek tamamlandı",  "percent:25"),
        Milestone("Yarı tamamlandı",    "percent:50"),
        Milestone("Dörtte üç tamamlandı", "percent:75"),
        Milestone("Sprint tamamlandı",  "percent:100"),
    ]
    # Kritik görevler için özel milestone
    for task in tasks:
        if task.get("critical"):
            milestones.append(Milestone(
                name=f"Kritik: {task.get('description', '')[:30]}",
                trigger=f"task:{task['id']}",
            ))
    return milestones

def check_milestones(
    milestones: list[Milestone],
    state: dict,
) -> list[Milestone]:
    tasks = state.get("tasks", [])
    total = len(tasks)
    done  = sum(1 for t in tasks if t.get("status") == "done")
    pct   = (done / total * 100) if total else 0
    
    newly_reached = []
    for m in milestones:
        if m.reached_at:
            continue
        if m.trigger.startswith("percent:"):
            threshold = float(m.trigger.split(":")[1])
            if pct >= threshold:
                m.reached_at = datetime.utcnow().isoformat()
                newly_reached.append(m)
        elif m.trigger.startswith("task:"):
            task_id = m.trigger.split(":")[1]
            task = next((t for t in tasks if t.get("id") == task_id), None)
            if task and task.get("status") == "done":
                m.reached_at = datetime.utcnow().isoformat()
                newly_reached.append(m)
    
    return newly_reached
```

---

## References

- `sprint-note-taking-skill/SKILL.md` — sprint not alma
- `sprint-stakeholder-update-skill/SKILL.md` — paydaş güncellemesi
- `progress-report-generation-skill/SKILL.md` — ilerleme raporu
