---
name: sprint-work-breakdown
description: Planner AI için — sprint görevlerini WBS (Work Breakdown Structure) hiyerarşisinde organize etmek; epic → story → task ağaç yapısı.
---

## Purpose

Düz görev listesi büyüdükçe yönetilemez hâle gelir.
WBS: görevleri hiyerarşik gruplar hâlinde düzenler.
Epic (büyük özellik) → Story (kullanıcı değeri) → Task (tek dosya) sırası.

---

## When to Apply

- 10'dan fazla görev içeren sprint planlanırken
- Büyük özellik birden fazla alt bileşen içerdiğinde
- Raporlamada görev grupları ayrı ayrı takip edilirken

---

## Rules

- Epic: en üst seviye, birden fazla story içerir.
- Story: kullanıcı değeri, birkaç task içerir.
- Task: tek dosya, tek geliştirici, max 30 dakika.
- Hiyerarşi: maks 3 seviye.

---

## Guidelines

```python
from dataclasses import dataclass, field

@dataclass
class WBSNode:
    id:       str
    title:    str
    level:    int  # 0=epic, 1=story, 2=task
    children: list["WBSNode"] = field(default_factory=list)
    task_ref: dict | None = None  # Leaf node için görev referansı

def build_wbs(epics: list[dict]) -> list[WBSNode]:
    nodes = []
    for epic in epics:
        epic_node = WBSNode(id=epic["id"], title=epic["title"], level=0)
        for story in epic.get("stories", []):
            story_node = WBSNode(id=story["id"], title=story["title"], level=1)
            for task in story.get("tasks", []):
                task_node = WBSNode(id=task["id"], title=task["description"], level=2, task_ref=task)
                story_node.children.append(task_node)
            epic_node.children.append(story_node)
        nodes.append(epic_node)
    return nodes

def flatten_tasks(wbs: list[WBSNode]) -> list[dict]:
    tasks = []
    def walk(node: WBSNode):
        if node.task_ref:
            tasks.append(node.task_ref)
        for child in node.children:
            walk(child)
    for n in wbs:
        walk(n)
    return tasks

def format_wbs(wbs: list[WBSNode], indent: int = 0) -> str:
    lines = []
    for node in wbs:
        prefix = "  " * indent
        icon   = ["📦", "📋", "📄"][min(node.level, 2)]
        lines.append(f"{prefix}{icon} {node.title}")
        lines.extend(format_wbs(node.children, indent + 1).splitlines())
    return "\n".join(lines)
```

---

## References

- `sprint-goal-decomposition-skill/SKILL.md` — hedef parçalama
- `sprint-user-story-mapping-skill/SKILL.md` — kullanıcı hikayesi
- `feature-breakdown-skill/SKILL.md` — özellik parçalama
