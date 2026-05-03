---
name: sprint-pause-resume
description: Planner AI için — aktif sprint'i geçici olarak durdurmak ve daha sonra kaldığı yerden devam ettirmek; HITL checkpoint mekanizmasını kullanmak.
---

## Purpose

Kullanıcı "şimdilik dur, yarın devam edelim" diyebilir.
Pause durumunda aktif worker'lar tamamlanır; yeni başlatılmaz.
Resume ile checkpoint'ten devam edilir — başa dönülmez.

---

## When to Apply

- Kullanıcı "dur/beklet/ertele" komutu verdiğinde
- Daemon restart nedeniyle otomatik pause gerektiğinde
- Sprint'i daha sonra devam ettirmek için güvenli duraklama noktası oluşturulurken

---

## Rules

- Pause: yeni dosya dağıtımı durdurulur, devam eden biter.
- `sprint_status = "paused"` ile işaretlenir.
- Resume: `ainvoke(None, config)` ile checkpoint'ten devam.
- Paused sprint `active` durumuna geri döner resume ile.

---

## Guidelines

```python
async def pause_sprint(
    project_id: str,
    repo: ProjectRepository,
    compiled_graph,
) -> None:
    config = get_thread_config(project_id)
    
    # Yeni dispatch'i engelle
    await compiled_graph.aupdate_state(
        config=config,
        values={"sprint_paused": True}
    )
    
    # Aktif sprint'i paused yap
    sprint = await repo.get_active_sprint(project_id)
    if sprint:
        await repo.update_sprint_status(sprint.sprint_id, "paused")
    
    logger.info(f"Sprint duraklatıldı: {project_id}")

async def resume_sprint(
    project_id: str,
    repo: ProjectRepository,
    compiled_graph,
) -> None:
    config = get_thread_config(project_id)
    
    # Pause bayrağını kaldır
    await compiled_graph.aupdate_state(
        config=config,
        values={"sprint_paused": False}
    )
    
    # Sprint'i active yap
    sprint = await repo.get_active_sprint(project_id)
    if sprint:
        await repo.update_sprint_status(sprint.sprint_id, "active")
    
    # Checkpoint'ten devam
    await compiled_graph.ainvoke(None, config=config)
    logger.info(f"Sprint devam ettiriliyor: {project_id}")
```

PM mesaj formatı:
```
[SOHBET] Sprint duraklatıldı.

Devam eden 2 görev tamamlanıyor...
Yeni görev başlatılmayacak.

Devam etmek için: "devam et" veya /resume
```

---

## References

- `partial-sprint-recovery-skill/SKILL.md` — recovery
- `sprint-lifecycle-state-machine-skill/SKILL.md` — durum
- `thread-config-usage-skill/SKILL.md` — checkpoint
