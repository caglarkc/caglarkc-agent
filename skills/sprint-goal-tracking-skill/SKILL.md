---
name: sprint-goal-tracking
description: Planner AI için — sprint boyunca hedefin hâlâ geçerli olup olmadığını izlemek; kapsam değişikliğinde hedefi güncellemek.
---

## Purpose

Sprint başlangıcındaki hedef sprint sırasında değişebilir.
Hedef takibi: orijinal hedef korunur, değişiklikler versiyonlanır.
Son hâl her zaman görünür, neden değiştiği kayıt altında.

---

## When to Apply

- Sprint sırasında kullanıcı hedefi güncellediğinde
- Kapsam genişlemesi tespit edildiğinde
- Sprint özeti hazırlanırken orijinal vs. tamamlanan karşılaştırılırken

---

## Rules

- Orijinal hedef: sprint başında snapshot, değiştirilemez.
- Aktif hedef: güncellenebilir, her değişiklik versiyonlanır.
- Değişiklik sebebi: zorunlu alan.
- Versiyon geçmişi: maks 5 (eski olanlar arşivlenir).

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class GoalRevision:
    version:    int
    goal:       str
    reason:     str
    revised_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

def initialize_goal_tracking(state: dict) -> dict:
    goal = state.get("sprint_goal", "")
    return {
        "original_goal":  goal,
        "goal_revisions": [
            {"version": 1, "goal": goal, "reason": "Sprint başlangıcı", "revised_at": datetime.utcnow().isoformat()}
        ],
    }

def update_sprint_goal(
    state: dict,
    new_goal: str,
    reason: str,
) -> dict:
    revisions = list(state.get("goal_revisions", []))
    next_ver  = len(revisions) + 1
    
    revisions.append({
        "version":    next_ver,
        "goal":       new_goal,
        "reason":     reason,
        "revised_at": datetime.utcnow().isoformat(),
    })
    
    # Max 5 revizyon tut
    if len(revisions) > 5:
        revisions = revisions[-5:]
    
    return {
        "sprint_goal":    new_goal,
        "goal_revisions": revisions,
    }

def format_goal_history(state: dict) -> str:
    original  = state.get("original_goal", "")
    current   = state.get("sprint_goal", "")
    revisions = state.get("goal_revisions", [])
    
    lines = [f"Orijinal hedef: {original}"]
    if current != original:
        lines.append(f"Güncel hedef : {current}")
        lines.append(f"\nRevizyon geçmişi ({len(revisions)}):")
        for r in revisions[1:]:
            lines.append(f"  v{r['version']}: {r['goal'][:50]} ({r['reason']})")
    return "\n".join(lines)
```

---

## References

- `sprint-goal-validation-skill/SKILL.md` — hedef doğrulama
- `sprint-scope-negotiation-skill/SKILL.md` — kapsam müzakeresi
- `sprint-note-taking-skill/SKILL.md` — sprint notları
