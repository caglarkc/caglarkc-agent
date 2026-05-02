---
name: task-estimation-calibration
description: Planner AI için — geçmiş sprint verilerine göre görev süresi tahminlerini kalibre etmek; tutarlı ve gerçekçi beklenti yönetimi yapmak.
---

## Purpose

"Bu görev 1 saat sürer" tahmini gerçekten 3 saat sürerse güven kırılır.
Geçmiş sprint metrikleri tahmin kalibrasyonu için kullanılır.
Kalibrasyon: benzer görevlerin gerçek süresi baz alınır.

---

## When to Apply

- Sprint planlanırken süre tahmini yapılırken
- Çok büyük görev küçük görevlere bölünmesi değerlendirilirken
- Sprint velocity hesaplanırken

---

## Rules

- Tahmin yok, karmaşıklık skoru var: S/M/L/XL.
- S: 1-3 dosya, basit ekleme.
- M: 4-7 dosya, yeni modül.
- L: 8+ dosya, mimari değişiklik.
- XL: sprint bölünmeli.
- Geçmiş veritabanı yoksa default tahmin kullanılır.

---

## Guidelines

```python
from enum import Enum

class TaskComplexity(str, Enum):
    S  = "S"   # Small
    M  = "M"   # Medium
    L  = "L"   # Large
    XL = "XL"  # Extra Large — sprint bölünmeli

def estimate_task_complexity(task: dict) -> TaskComplexity:
    file_count = len(task.get("files", []))
    desc = task.get("description", "").lower()
    
    is_architectural = any(
        k in desc for k in
        ["mimari", "graph", "refactor", "yeniden yaz", "migrate"]
    )
    
    if is_architectural or file_count >= 8:
        return TaskComplexity.XL if file_count >= 15 else TaskComplexity.L
    elif file_count >= 4:
        return TaskComplexity.M
    else:
        return TaskComplexity.S

def estimate_sprint_complexity(tasks: list[dict]) -> str:
    complexities = [estimate_task_complexity(t) for t in tasks]
    xl_count = complexities.count(TaskComplexity.XL)
    l_count = complexities.count(TaskComplexity.L)
    
    if xl_count > 0:
        return "Çok büyük — sprint bölünmeli"
    elif l_count > 1:
        return "Büyük — dikkatli planlama gerekli"
    elif l_count == 1:
        return "Orta-büyük"
    else:
        return "Normal"

# PM sunum
COMPLEXITY_LABELS = {
    TaskComplexity.S:  "Küçük (1-3 dosya)",
    TaskComplexity.M:  "Orta (4-7 dosya)",
    TaskComplexity.L:  "Büyük (8+ dosya)",
    TaskComplexity.XL: "Çok büyük — bölünmeli",
}
```

---

## References

- `sprint-budget-estimation-skill/SKILL.md` — büyüklük tahmini
- `sprint-metrics-collection-skill/SKILL.md` — geçmiş veriler
- `feature-breakdown-skill/SKILL.md` — özellik ayrıştırma
