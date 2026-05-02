---
name: sprint-multi-goal
description: Planner AI için — tek sprint'te birden fazla hedefi yönetmek; her hedef için ayrı görev grubu oluşturmak.
---

## Purpose

Tek hedefli sprint bazen yeterli değil — "hem DB hem API ekle" istenebilir.
Multi-goal: her hedef kendi görev grubu ve durumuna sahip.
İlerleme: hedef bazında raporlanır.

---

## When to Apply

- Kullanıcı tek seferde birden fazla özellik istediğinde
- İlgili hedefler aynı dosyalara dokunduğunda birlikte planlamak verimliyken
- Birbirinden bağımsız iki modül aynı sprintte geliştirilebilirken

---

## Rules

- Hedef sayısı: maks 3 (daha fazla = ayrı sprint).
- Her hedef: bağımsız görev listesi.
- Çakışan dosya: `sprint-conflict-resolution` ile çözülür.
- Raporlama: "Hedef 1: %100, Hedef 2: %60" formatında.

---

## Guidelines

```python
from dataclasses import dataclass, field

@dataclass
class SprintGoal:
    goal_id:     str
    description: str
    tasks:       list[str] = field(default_factory=list)  # task id'leri
    status:      str = "pending"  # pending | in_progress | done | failed

def initialize_multi_goal_sprint(
    goals: list[str],
    tasks_per_goal: list[list[dict]],
) -> dict:
    sprint_goals = []
    all_tasks    = []
    
    for i, (goal, tasks) in enumerate(zip(goals, tasks_per_goal)):
        goal_id = f"goal_{i+1}"
        for task in tasks:
            task["goal_id"] = goal_id
        
        sprint_goals.append(SprintGoal(
            goal_id=goal_id,
            description=goal,
            tasks=[t["id"] for t in tasks],
        ))
        all_tasks.extend(tasks)
    
    return {
        "sprint_goals": [g.__dict__ for g in sprint_goals],
        "tasks":        all_tasks,
    }

def compute_goal_progress(state: dict) -> list[dict]:
    tasks     = {t["id"]: t for t in state.get("tasks", [])}
    progress  = []
    
    for goal in state.get("sprint_goals", []):
        goal_tasks = [tasks.get(tid) for tid in goal["tasks"] if tasks.get(tid)]
        total   = len(goal_tasks)
        done    = sum(1 for t in goal_tasks if t and t.get("status") == "done")
        pct     = int(done / total * 100) if total else 0
        
        progress.append({
            "goal_id":     goal["goal_id"],
            "description": goal["description"],
            "progress":    pct,
            "done":        done,
            "total":       total,
        })
    
    return progress

def format_multi_goal_progress(progress: list[dict]) -> str:
    lines = ["Sprint İlerlemesi (Çoklu Hedef):"]
    for p in progress:
        bar = "█" * (p["progress"] // 10) + "░" * (10 - p["progress"] // 10)
        lines.append(f"  {p['description'][:40]:40} [{bar}] %{p['progress']}")
    return "\n".join(lines)
```

---

## References

- `sprint-goal-decomposition-skill/SKILL.md` — hedef parçalama
- `sprint-conflict-resolution-skill/SKILL.md` — çakışma çözümü
- `sprint-capacity-planning-skill/SKILL.md` — kapasite planlaması
