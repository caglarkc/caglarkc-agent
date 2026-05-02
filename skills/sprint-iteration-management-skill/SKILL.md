---
name: sprint-iteration-management
description: Planner AI için — sprint içinde iterasyonları yönetmek; başarısız dosyaları sonraki iterasyona taşımak.
---

## Purpose

Tek geçişte tüm dosyaları üretmek her zaman mümkün değil.
İterasyon yönetimi: başarısız görevler 2. geçişte tekrar denenir.
Her iterasyon: önceki hataların öğrenimi ile daha iyi çalışır.

---

## When to Apply

- İlk sprint geçişinde bazı dosyalar başarısız olduğunda
- Validator birden fazla kez "tekrar dene" kararı verdiğinde
- İteratif kod üretimi döngüsü tasarlanırken

---

## Rules

- Max iterasyon: 3.
- Her iterasyonda: yalnızca başarısız görevler yeniden denenir.
- Öğrenme: önceki hata mesajı bir sonraki prompte eklenir.
- 3. iterasyon sonrası hâlâ başarısız: `failed_permanently`.

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class IterationState:
    iteration:      int = 1
    max_iterations: int = 3

def get_retry_tasks(state: dict) -> list[dict]:
    return [
        t for t in state.get("tasks", [])
        if t.get("status") == "failed" and
           t.get("retry_count", 0) < state.get("max_iterations", 3)
    ]

def prepare_next_iteration(state: dict) -> dict:
    iter_no = state.get("current_iteration", 1) + 1
    retry   = get_retry_tasks(state)
    
    if not retry or iter_no > state.get("max_iterations", 3):
        return {"sprint_status": "iteration_complete"}
    
    # Başarısız görevleri sıfırla
    tasks = list(state.get("tasks", []))
    for task in tasks:
        if task.get("status") == "failed":
            task["status"]      = "planned"
            task["iteration"]   = iter_no
            task["prev_error"]  = task.get("last_error", "")
            task["retry_count"] = task.get("retry_count", 0) + 1
    
    return {
        "tasks":             tasks,
        "current_iteration": iter_no,
        "sprint_status":     "running",
    }

def add_error_context_to_prompt(task: dict, base_prompt: str) -> str:
    prev_error = task.get("prev_error")
    if not prev_error:
        return base_prompt
    return (
        f"{base_prompt}\n\n"
        f"Önceki denemede şu hata oluştu:\n{prev_error}\n"
        f"Bu hatayı düzelt."
    )
```

---

## References

- `sprint-restart-skill/SKILL.md` — sprint yeniden başlatma
- `retry-decision-logic-skill/SKILL.md` — retry kararı
- `dead-letter-queue-skill/SKILL.md` — başarısız görev kuyruğu
