---
name: sprint-task-splitting
description: Planner AI için — tahmini süresi fazla olan büyük görevi otomatik olarak daha küçük alt görevlere bölmek.
---

## Purpose

30 dakikadan uzun görev tahmin doğruluğunu düşürür.
Görev bölme: büyük görevi 2-3 bağımlı alt göreve parçalar.
Her alt görev: tek dosya, net çıktı, max 20 dakika.

---

## When to Apply

- Tahmin edilen süre 30 dakikayı aştığında
- Görev birden fazla dosyaya dokunduğunda
- LLM tek seferde üretemeyeceği kadar büyük kod istendiğinde

---

## Rules

- Bölme eşiği: 30 dakika.
- Alt görev sayısı: 2-4.
- Bağımlılık: alt görevler sıralı bağımlılık zinciri oluşturabilir.
- ID: `parent_id + "_sub{n}"` formatında.

---

## Guidelines

```python
SPLIT_PROMPT = """
Şu görev çok büyük (tahmini {minutes} dakika). 2-4 alt göreve böl.
Her alt görev: tek dosya, max 20 dakika, net çıktı.

Görev: {description}
Dosya: {file_path}

JSON:
{{"sub_tasks": [{{"id": "...", "description": "...", "file_path": "...", "estimated_minutes": N, "depends_on": []}}]}}
"""

async def maybe_split_task(
    task: dict,
    llm,
    threshold_minutes: int = 30,
) -> list[dict]:
    if task.get("estimated_minutes", 0) <= threshold_minutes:
        return [task]

    prompt = SPLIT_PROMPT.format(
        minutes=task["estimated_minutes"],
        description=task.get("description", ""),
        file_path=task.get("file_path", ""),
    )
    response = await llm.ainvoke([{"role": "user", "content": prompt}])

    import json, re
    match = re.search(r'\{.*\}', response.content, re.DOTALL)
    if not match:
        return [task]

    try:
        data = json.loads(match.group())
        sub_tasks = data.get("sub_tasks", [])
        parent_id = task["id"]
        for i, st in enumerate(sub_tasks, 1):
            st["id"]        = f"{parent_id}_sub{i}"
            st["parent_id"] = parent_id
        return sub_tasks if sub_tasks else [task]
    except json.JSONDecodeError:
        return [task]
```

---

## References

- `sprint-goal-decomposition-skill/SKILL.md` — hedef parçalama
- `feature-breakdown-skill/SKILL.md` — özellik parçalama
- `task-estimation-calibration-skill/SKILL.md` — tahmin kalibrasyonu
