---
name: sprint-multi-agent-coordination
description: Planner AI için — birden fazla AI ajanın (planner + coder) koordinasyonunu yönetmek; görev dağılımı ve iletişim protokolü.
---

## Purpose

Planner ve Coder farklı LLM'ler — birbirine doğrudan mesaj gönderemez.
Koordinasyon: state üzerinden mesajlaşma, görev sözleşmesi, çıktı formatı.
Her ajan kendi rolünü bilir, aşmaz.

---

## When to Apply

- Planner node ile worker node arasındaki sözleşme tanımlanırken
- Çok ajanlı sistemde rollerin netleştirilmesi gerektiğinde
- Ajan çıktısını diğer ajan input olarak kullanırken

---

## Rules

- Mesajlaşma: state üzerinden (doğrudan çağrı değil).
- Planner → Worker: task dict (standart format).
- Worker → Planner: result dict (dosya, durum, hata).
- Rol ihlali: worker plan değiştirmez, planner kod yazmaz.

---

## Guidelines

```python
from typing import TypedDict

class PlannerToWorkerMessage(TypedDict):
    task_id:            str
    description:        str
    file_path:          str
    context_files:      dict[str, str]
    style_guidelines:   str
    estimated_minutes:  int
    prev_error:         str | None

class WorkerToPlannerMessage(TypedDict):
    task_id:      str
    file_path:    str
    status:       str  # "done" | "failed"
    error:        str | None
    generated:    bool
    retry_hint:   str | None

def planner_creates_message(task: dict, context: dict) -> PlannerToWorkerMessage:
    return PlannerToWorkerMessage(
        task_id=task["id"],
        description=task.get("description", ""),
        file_path=task.get("file_path", ""),
        context_files=context.get("context_files", {}),
        style_guidelines=context.get("style_guidelines", ""),
        estimated_minutes=task.get("estimated_minutes", 20),
        prev_error=task.get("prev_error"),
    )

def worker_creates_result(
    task_id: str,
    file_path: str,
    success: bool,
    error: str | None = None,
) -> WorkerToPlannerMessage:
    return WorkerToPlannerMessage(
        task_id=task_id,
        file_path=file_path,
        status="done" if success else "failed",
        error=error,
        generated=success,
        retry_hint="Prompt netleştir" if error and "syntax" in str(error).lower() else None,
    )

def update_state_from_worker_result(
    state: dict,
    result: WorkerToPlannerMessage,
) -> dict:
    registry = dict(state.get("file_registry", {}))
    registry[result["file_path"]] = result["status"]
    tasks = list(state.get("tasks", []))
    for t in tasks:
        if t["id"] == result["task_id"]:
            t["status"] = result["status"]
            if result["error"]:
                t["last_error"] = result["error"]
    return {"file_registry": registry, "tasks": tasks}
```

---

## References

- `worker-assignment-strategy-skill/SKILL.md` — worker atama
- `dispatcher-node-implementation-skill/SKILL.md` — dispatcher
- `message-bus-design-skill/SKILL.md` — mesaj otobüsü
