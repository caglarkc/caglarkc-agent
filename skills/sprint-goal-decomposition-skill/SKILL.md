---
name: sprint-goal-decomposition
description: Planner AI için — yüksek seviyeli sprint hedefini somut, eyleme geçirilebilir görevlere parçalamak.
---

## Purpose

"Kullanıcı yönetimi ekle" tek bir hedef ama onlarca alt görev içerir.
Decomposition: hedefi bağımsız uygulanabilir parçalara böler.
Her parça: tek sorumluluk, net çıktı, bağımlılıkları belirtilmiş.

---

## When to Apply

- Kullanıcı yüksek seviyeli bir özellik istediğinde
- Sprint hedefi somut görevlere çevrilirken
- Büyük refactor veya yeni modül planlanırken

---

## Rules

- Görev: tek bir dosya veya fonksiyon değişikliği.
- Maks görev başına tahmini süre: 30 dakika.
- Bağımlılıklar açık belirtilir (başka hangi görev tamamlanmalı).
- Toplam görev: 20'yi geçmemeli (yönetilebilir tutulur).

---

## Guidelines

```python
DECOMPOSE_PROMPT = """
Şu sprint hedefini somut görevlere parçala.
Her görev tek bir Python dosyasına dokunmalı.
Bağımlılıkları (hangi görev önce bitmeli) belirt.
JSON formatında döndür.

Sprint hedefi: {goal}
Mevcut dosyalar: {existing_files}

Çıktı formatı:
{{
  "tasks": [
    {{
      "id": "task_001",
      "description": "...",
      "file_path": "src/...",
      "depends_on": [],
      "estimated_minutes": 20
    }}
  ]
}}
"""

def validate_decomposition(tasks: list[dict]) -> list[str]:
    errors = []
    ids = {t["id"] for t in tasks}
    
    for task in tasks:
        if not task.get("file_path"):
            errors.append(f"{task['id']}: file_path eksik")
        for dep in task.get("depends_on", []):
            if dep not in ids:
                errors.append(f"{task['id']}: bilinmeyen bağımlılık {dep}")
        if task.get("estimated_minutes", 0) > 60:
            errors.append(f"{task['id']}: görev çok büyük (>60dk)")
    
    return errors

def order_tasks_by_dependency(tasks: list[dict]) -> list[dict]:
    """Topolojik sıralama."""
    order, visited = [], set()
    task_map = {t["id"]: t for t in tasks}
    
    def visit(task_id: str):
        if task_id in visited:
            return
        visited.add(task_id)
        for dep in task_map.get(task_id, {}).get("depends_on", []):
            visit(dep)
        order.append(task_map[task_id])
    
    for t in tasks:
        visit(t["id"])
    return order
```

---

## References

- `feature-breakdown-skill/SKILL.md` — özellik parçalama
- `task-dependency-ordering-skill/SKILL.md` — bağımlılık sıralaması
- `sprint-budget-estimation-skill/SKILL.md` — bütçe tahmini
