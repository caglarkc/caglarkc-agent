---
name: multi-sprint-backlog
description: Planner AI için — birden fazla sprint için backlog tutmak; önceliklendirme ve sıradaki sprint seçimi.
---

## Purpose

Tek sprint planlanır, diğer istekler unutulur.
Backlog: tüm bekleyen sprint hedeflerini saklar, önceliklendirir.
Sıradaki sprint otomatik veya kullanıcı seçimiyle backlog'dan gelir.

---

## When to Apply

- Kullanıcı birden fazla özellik istediğinde
- Sprint tamamlandıktan sonra sıradaki belirlenmek istediğinde
- Uzun vadeli proje planı yapılırken

---

## Rules

- Backlog: liste, FIFO veya öncelik sırasına göre.
- Her backlog öğesi: hedef, öncelik (1-5), oluşturma tarihi.
- Tamamlanan sprint backlog'dan çıkarılır.
- Backlog görüntüleme isteğinde ilk 10 öğe gösterilir.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class BacklogItem:
    goal:        str
    priority:    int = 3  # 1=en yüksek, 5=en düşük
    created_at:  datetime = field(default_factory=datetime.utcnow)
    tags:        list[str] = field(default_factory=list)
    item_id:     str = field(default_factory=lambda: str(__import__("uuid").uuid4())[:8])

def add_to_backlog(
    state: dict,
    goal: str,
    priority: int = 3,
    tags: list[str] | None = None,
) -> dict:
    backlog = list(state.get("backlog", []))
    item = BacklogItem(goal=goal, priority=priority, tags=tags or [])
    backlog.append({
        "id":       item.item_id,
        "goal":     goal,
        "priority": priority,
        "tags":     item.tags,
        "created":  item.created_at.isoformat(),
    })
    backlog.sort(key=lambda x: x["priority"])
    return {"backlog": backlog}

def pop_next_sprint_goal(state: dict) -> tuple[str | None, dict]:
    backlog = list(state.get("backlog", []))
    if not backlog:
        return None, {}
    next_item = backlog.pop(0)
    return next_item["goal"], {"backlog": backlog}

def format_backlog(backlog: list[dict]) -> str:
    if not backlog:
        return "Backlog boş."
    lines = [f"Backlog ({len(backlog)} öğe):"]
    for i, item in enumerate(backlog[:10], 1):
        lines.append(f"  {i}. [P{item['priority']}] {item['goal'][:60]}")
    return "\n".join(lines)
```

---

## References

- `sprint-auto-continuation-skill/SKILL.md` — otomatik devam
- `sprint-priority-matrix-skill/SKILL.md` — öncelik matrisi
- `sprint-goal-validation-skill/SKILL.md` — hedef doğrulama
