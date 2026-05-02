---
name: workflow-visualization
description: Planner AI için — sprint akışını ve görev bağımlılıklarını ASCII veya Mermaid diyagramıyla görselleştirerek kullanıcıya sunmak.
---

## Purpose

Soyut görev listesi yerine görsel akış daha kolay anlaşılır.
Kullanıcı onaylamadan önce ne yapılacağını net görmek ister.
Mermaid diyagramı terminal veya Telegram'da renderable.

---

## When to Apply

- Sprint planı kullanıcıya sunulmadan önce
- Görev bağımlılıkları karmaşık olduğunda
- "Nasıl çalışacak?" sorusu geldiğinde

---

## Rules

- ASCII: terminal uyumlu, her zaman çalışır.
- Mermaid: markdown render'da görünür.
- Maksimum 8 node — daha fazlası diyagramı karmaşık yapar.
- Dosya yolları kısaltılır: `src/graph/nodes/planner.py` → `planner.py`.

---

## Guidelines

```python
def generate_task_flow_ascii(tasks: list[dict]) -> str:
    lines = ["Sprint Akışı:"]
    lines.append("─" * 40)
    
    for i, task in enumerate(tasks, 1):
        deps = task.get("depends_on", [])
        dep_str = f" (← {', '.join(deps)})" if deps else ""
        lines.append(f"{i}. {task['description'][:40]}{dep_str}")
        
        files = task.get("files", [])
        for f in files[:3]:
            fname = f.split("/")[-1]
            lines.append(f"   └─ {fname}")
        if len(files) > 3:
            lines.append(f"   └─ ... +{len(files)-3} dosya")
    
    return "\n".join(lines)

def generate_mermaid_diagram(tasks: list[dict]) -> str:
    lines = ["```mermaid", "graph TD"]
    
    for task in tasks:
        task_id = task["task_id"].replace("-", "_")
        label = task["description"][:30].replace('"', "'")
        lines.append(f'    {task_id}["{label}"]')
        
        for dep in task.get("depends_on", []):
            dep_id = dep.replace("-", "_")
            lines.append(f"    {dep_id} --> {task_id}")
    
    lines.append("```")
    return "\n".join(lines)
```

PM'in sunum formatı:
```
[PLANLAMA] Sprint 4 Akışı:

───────────────────────
1. Temel modeller
   └─ models.py
2. Repository (← 1)
   └─ repository.py
3. Servis katmanı (← 2)
   └─ service.py
───────────────────────

Bu sırayla çalışacak. Onaylıyor musunuz?
```

---

## References

- `task-dependency-ordering-skill/SKILL.md` — görev sırası
- `sprint-plan-revision-skill/SKILL.md` — plan revizyonu
- `output-formatting-skill/SKILL.md` — çıktı formatı
