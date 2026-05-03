---
name: sprint-constraint-solver
description: Planner AI için — sprint kısıtlamalarını (süre, worker, token) göz önüne alarak gerçekçi görev seçimi yapmak.
---

## Purpose

Tüm görevler sığmaz — kısıtlar içinde en yüksek değeri almak gerekir.
Kısıt çözücü: öncelik ve tahminlere göre kapasite içindeki en iyi görev setini seçer.
Knapsack benzeri yaklaşım: ağırlık=süre, değer=öncelik.

---

## When to Apply

- Sprint kapasitesi tüm görevlere yetmediğinde
- Kaynak kısıtı altında öncelikli görevler seçilirken
- `sprint-capacity-planning` aşım uyarısı verdiğinde

---

## Rules

- Algoritma: greedy (öncelik/süre oranına göre sırala).
- Seçilmeyenler: backlog'a eklenir, kaybedilmez.
- Bağımlılıklar: bağımlı görev seçilirse bağımlılığı da seçilir.
- Çıktı: seçilen + ertelenen görev listesi.

---

## Guidelines

```python
def solve_sprint_constraints(
    tasks: list[dict],
    capacity_minutes: float,
) -> tuple[list[dict], list[dict]]:
    # Bağımlılıkları çöz: bir görev seçilirse tüm bağımlılıkları da seçilmeli
    task_map = {t["id"]: t for t in tasks}

    def with_deps(task_id: str, seen: set | None = None) -> list[str]:
        seen = seen or set()
        if task_id in seen:
            return []
        seen.add(task_id)
        task = task_map.get(task_id, {})
        result = []
        for dep in task.get("depends_on", []):
            result.extend(with_deps(dep, seen))
        result.append(task_id)
        return result

    # Öncelik/süre oranına göre sırala (yüksek değer = önce)
    scored = sorted(
        tasks,
        key=lambda t: (6 - t.get("priority", 3)) / max(t.get("estimated_minutes", 1), 1),
        reverse=True,
    )

    selected_ids: set[str] = set()
    used_minutes = 0.0

    for task in scored:
        chain = with_deps(task["id"])
        chain_mins = sum(task_map.get(tid, {}).get("estimated_minutes", 0) for tid in chain)
        if used_minutes + chain_mins <= capacity_minutes:
            selected_ids.update(chain)
            used_minutes += chain_mins

    selected = [t for t in tasks if t["id"] in selected_ids]
    deferred = [t for t in tasks if t["id"] not in selected_ids]
    return selected, deferred
```

---

## References

- `sprint-capacity-planning-skill/SKILL.md` — kapasite planlaması
- `sprint-priority-matrix-skill/SKILL.md` — öncelik matrisi
- `multi-sprint-backlog-skill/SKILL.md` — çoklu sprint backlog
