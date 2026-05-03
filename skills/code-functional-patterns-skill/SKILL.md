---
name: code-functional-patterns
description: Coder AI için — Python'da fonksiyonel programlama kalıplarını uygulamak; map, filter, reduce, partial ve compose kullanımı.
---

## Purpose

Döngü ve mutable state karmaşıklığı artırır.
Fonksiyonel kalıplar: daha kısa, test edilebilir, yan etkisiz kod.
LangGraph pipeline ve veri dönüşümleri için özellikle uygun.

---

## When to Apply

- Koleksiyon dönüşümleri yapılırken
- Pipeline adımları fonksiyon olarak zincirlenmek istendiğinde
- Konfigürasyon veya factory pattern oluşturulurken

---

## Rules

- Saf fonksiyon: aynı girdi → aynı çıktı, yan etki yok.
- `map/filter`: kısa, açık dönüşümler için.
- `functools.reduce`: toplama, birleştirme için.
- `functools.partial`: bağımsız değişken bağlama için.

---

## Guidelines

```python
from functools import reduce, partial
from typing import Callable, TypeVar

T = TypeVar("T")
U = TypeVar("U")

def compose(*fns: Callable) -> Callable:
    return reduce(lambda f, g: lambda x: g(f(x)), fns)

def pipe(value, *fns: Callable):
    return reduce(lambda v, f: f(v), fns, value)

# Sprint state dönüşüm pipeline'ı
def filter_planned(tasks: list[dict]) -> list[dict]:
    return [t for t in tasks if t.get("status") == "planned"]

def sort_by_priority(tasks: list[dict]) -> list[dict]:
    return sorted(tasks, key=lambda t: t.get("priority", 3))

def take_n(n: int) -> Callable[[list], list]:
    return lambda items: items[:n]

# Compose ile pipeline
get_next_tasks = compose(
    filter_planned,
    sort_by_priority,
    take_n(3),
)

# Partial: parametreli fonksiyon sabitleme
def update_task_status(status: str, task: dict) -> dict:
    return {**task, "status": status}

mark_done    = partial(update_task_status, "done")
mark_failed  = partial(update_task_status, "failed")
mark_running = partial(update_task_status, "in_progress")

# Kullanım
completed = list(map(mark_done, done_tasks))

# Reduce: state birleştirme
def merge_states(acc: dict, patch: dict) -> dict:
    return {**acc, **patch}

final_state = reduce(merge_states, patches, initial_state)
```

---

## References

- `code-generator-function-skill/SKILL.md` — generator fonksiyon
- `batch-processing-skill/SKILL.md` — toplu işleme
- `llm-prompt-chaining-skill/SKILL.md` — prompt zincirleme
