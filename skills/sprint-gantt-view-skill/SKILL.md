---
name: sprint-gantt-view
description: Planner AI için — sprint görevlerini basit ASCII Gantt şeması olarak görselleştirmek; zaman çizelgesini sohbet ekranında göstermek.
---

## Purpose

Görev listesi zaman boyutunu göstermez.
ASCII Gantt: CLI/sohbet ortamında zaman çizelgesi çizer.
Bağımlılıklar görünür, paralel çalışabilecek görevler belli olur.

---

## When to Apply

- Sprint planı kullanıcıya sunulmadan önce görsel özet istendiğinde
- Bağımlılıkları olan çok görevli sprintte
- "Görevler nasıl sıralanacak?" sorusu yanıtlanırken

---

## Rules

- Çıktı: sadece ASCII, terminal genişliği 80 karakter.
- Zaman birimi: sütun başına 10 dakika.
- Paralel görevler: aynı satırda değil, üst üste gösterilmez.
- Bağımlılık: ok `→` ile gösterilir.

---

## Guidelines

```python
def build_gantt(tasks: list[dict], sprint_minutes: int = 60) -> str:
    col_size   = 10  # dakika / sütun
    cols       = sprint_minutes // col_size
    
    # Topolojik sıralama
    ordered = _sort_tasks(tasks)
    
    header = "Görev".ljust(30) + "".join(str(i*col_size).rjust(4) for i in range(cols // 4 + 1))
    lines  = [header, "-" * 80]
    
    cursor = 0
    for task in ordered:
        est   = task.get("estimated_minutes", 20)
        start = cursor
        end   = min(start + est // col_size + 1, cols)
        
        bar = " " * start + "█" * (end - start) + " " * (cols - end)
        name = task.get("description", task["id"])[:28].ljust(30)
        lines.append(name + bar)
        cursor = end
    
    return "\n".join(lines)

def _sort_tasks(tasks: list[dict]) -> list[dict]:
    order, visited = [], set()
    task_map = {t["id"]: t for t in tasks}
    
    def visit(tid):
        if tid in visited:
            return
        visited.add(tid)
        for dep in task_map.get(tid, {}).get("depends_on", []):
            visit(dep)
        order.append(task_map[tid])
    
    for t in tasks:
        visit(t["id"])
    return order

# Örnek çıktı:
# Görev                          0  10  20  30
# -----------------------------------------------
# DB şeması oluştur              ███
# Kullanıcı modeli yaz               ████
# API endpoint ekle                       ██████
```

---

## References

- `workflow-visualization-skill/SKILL.md` — iş akışı görselleştirme
- `sprint-dependency-graph-skill/SKILL.md` — bağımlılık grafiği
- `task-dependency-ordering-skill/SKILL.md` — görev sıralama
