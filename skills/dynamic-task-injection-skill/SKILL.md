---
name: dynamic-task-injection
description: Planner AI için — sprint çalışırken öngörülemeyen bağımlılık keşfedildiğinde yeni görev enjekte etmek; planı dondurulmamış tutmak.
---

## Purpose

Bazen worker "models.py gerekiyor ama yok" hatası verir.
Dinamik görev enjeksiyonu yeni görev ekleyip dosya_registry'yi günceller.
Sprint yeniden planlanmak yerine in-flight değiştirilir.

---

## When to Apply

- Worker bir bağımlılık dosyasının eksik olduğunu bildirdiğinde
- Validator beklenmedik import hatası tespit ettiğinde
- Planner ek görev eklenmesi gerektiğini anlayınca

---

## Rules

- Enjeksiyon: sadece `planned` aşamasında yapılabilir (henüz dispatch edilmemiş).
- Kullanıcıya bildirim yapılır ama onay istenmez (minor ekleme).
- Enjekte görev bağımlı görev önce işlenmeli — dispatcher sıralaması güncellenir.
- Max 3 enjeksiyon — daha fazlası planın yanlış olduğunu gösterir.

---

## Guidelines

```python
async def inject_task(
    state: OrchestratorState,
    compiled_graph,
    new_task: dict,
    new_files: list[str],
) -> None:
    config = get_thread_config(state["project_id"])
    
    # Mevcut tasks ve registry
    current_tasks = list(state.get("tasks", []))
    current_registry = dict(state.get("file_registry", {}))
    
    # Yeni görev ve dosyaları ekle
    current_tasks.insert(0, new_task)  # önce işlenecek
    for file_path in new_files:
        if file_path not in current_registry:
            current_registry[file_path] = "planned"
    
    injection_count = state.get("task_injection_count", 0) + 1
    
    if injection_count > 3:
        logger.warning("Max görev enjeksiyonu aşıldı — sprint yeniden planlanmalı")
        return
    
    await compiled_graph.aupdate_state(
        config=config,
        values={
            "tasks": current_tasks,
            "file_registry": current_registry,
            "task_injection_count": injection_count,
        }
    )
    
    logger.info(f"Görev enjekte edildi: {new_task['task_id']}")

# Kullanıcı bildirimi
def format_injection_notice(new_task: dict) -> str:
    return (
        f"[PLANLAMA] Eksik bağımlılık tespit edildi.\n\n"
        f"Yeni görev eklendi: {new_task['description']}\n"
        f"Dosya: {', '.join(new_task.get('files', []))}\n\n"
        f"Sprint devam ediyor..."
    )
```

---

## References

- `task-dependency-ordering-skill/SKILL.md` — görev sırası
- `file-status-state-machine-skill/SKILL.md` — dosya durumu
- `dispatcher-node-implementation-skill/SKILL.md` — dispatcher
