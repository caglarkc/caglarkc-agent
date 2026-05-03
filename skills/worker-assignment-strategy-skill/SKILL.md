---
name: worker-assignment-strategy
description: Planner AI için — hangi dosyanın hangi worker'a atanacağına karar vermek; önceliklendirme ve yük dengeleme.
---

## Purpose

Tüm dosyaları aynı worker'a vermek sıralı çalışmaya döner — paralel değil.
Bağımlılıkları olan dosyalar doğru sırayla worker'a verilmeli.
Yük dengeleme: karmaşık dosyalar tek worker'ı meşgul etmemeli.

---

## When to Apply

- Dispatcher dosyaları worker kuyruğuna eklerken
- `MAX_CONCURRENT_WORKERS` kapasitesi planlanırken
- Bağımlı ve bağımsız dosyalar gruplara ayrılırken

---

## Rules

- Bağımsız dosyalar: paralel worker'lara dağıtılır.
- Bağımlı dosya: önceki dosya `done` olmadan kuyruğa girmez.
- Büyük dosya (100+ satır LLM üretimi): önce işlenir.
- Worker kapasitesi doluysa: bekle, zorla atama yapma.

---

## Guidelines

```python
def assign_files_to_workers(
    planned_files: list[str],
    tasks: list[dict],
    max_workers: int = 3,
) -> list[list[str]]:
    """
    Dosyaları worker gruplarına atar.
    Returns: her worker için dosya listesi
    """
    # Bağımlılıkları ayır
    independent = []
    dependent = []
    
    task_files = {
        f: task
        for task in tasks
        for f in task.get("files", [])
    }
    
    for file_path in planned_files:
        task = task_files.get(file_path, {})
        if task.get("depends_on"):
            dependent.append(file_path)
        else:
            independent.append(file_path)
    
    # Round-robin dağıtım
    groups: list[list[str]] = [[] for _ in range(max_workers)]
    for i, f in enumerate(independent):
        groups[i % max_workers].append(f)
    
    # Bağımlı dosyalar en az yüklü worker'a
    for f in dependent:
        min_group = min(groups, key=len)
        min_group.append(f)
    
    return [g for g in groups if g]

# Dispatcher kullanımı
async def dispatch_with_strategy(
    state: OrchestratorState,
    compiled_graph,
) -> None:
    planned = [
        p for p, s in state["file_registry"].items()
        if s == "planned"
    ]
    
    worker_groups = assign_files_to_workers(
        planned, state["tasks"], max_workers=3
    )
    
    # Her grubu ayrı kuyruk entry olarak ekle
    entries = [
        build_queue_entry(sprint_id, task, files[0])
        for files in worker_groups
        for task in [find_task(state, files[0])]
    ]
```

---

## References

- `dispatcher-node-implementation-skill/SKILL.md` — dispatcher
- `task-dependency-ordering-skill/SKILL.md` — bağımlılık sırası
- `worker-load-balancing-strategy-skill/SKILL.md` — yük dengeleme
