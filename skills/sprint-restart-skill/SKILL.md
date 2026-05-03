---
name: sprint-restart
description: Planner AI için — başarısız veya iptal edilmiş sprint'i yeni planla yeniden başlatmak; eski state'i temizleyip taze başlangıç yapmak.
---

## Purpose

Başarısız sprint'ten sonra kullanıcı "tekrar dene" diyebilir.
Yeniden başlatma: eski sprint kapatılır, yeni sprint planlanır.
LangGraph checkpoint'te aynı thread_id ile resume yerine fresh start.

---

## When to Apply

- Sprint `cancelled` veya `failed` durumundayken "tekrar başlat" istendiğinde
- Aynı hedef için farklı yaklaşım denenmesi gerektiğinde
- Partial sprint result'ından "kaldığın yerden devam et" denildiğinde

---

## Rules

- Restart: eski sprint kapatılır (`cancelled` veya `failed`).
- Yeni sprint: yeni `sprint_id` ile.
- Kullanıcı yeni planı onaylar — eski plan tekrar kullanılmaz.
- Checkpoint: yeni thread_id ile başlatılabilir veya mevcut temizlenir.

---

## Guidelines

```python
async def restart_sprint(
    project_id: str,
    original_sprint_id: str,
    new_user_message: str,
    repo: ProjectRepository,
    compiled_graph,
) -> None:
    # Eski sprint'i kapat
    await repo.update_sprint_status(original_sprint_id, "cancelled")
    
    # Karar kaydet
    await repo.create_decision(Decision(
        project_id=project_id,
        sprint_id=original_sprint_id,
        summary=f"Sprint {original_sprint_id} yeniden başlatma sebebiyle kapatıldı",
        rationale="Kullanıcı sprint restart istedi",
        decision_type="cancellation",
    ))
    
    # Yeni sprint başlat
    config = get_thread_config(project_id)
    initial_state = build_initial_state(project_id, new_user_message)
    
    # State'i sıfırla (yeni thread veya reset)
    await compiled_graph.aupdate_state(
        config=config,
        values=initial_state,
    )
    
    # Planner'ı yeniden çalıştır
    await compiled_graph.ainvoke(initial_state, config=config)
    logger.info(f"Sprint yeniden başlatıldı: {project_id}")
```

PM mesaj:
```
[PLANLAMA] Sprint yeniden başlatılıyor...

Eski sprint (sprint-abc123) kapatıldı.
Yeni plan hazırlanıyor...

[ONAY-BEKLE] İşte yeni plan: ...
```

---

## References

- `sprint-cancellation-skill/SKILL.md` — iptal
- `state-initialization-skill/SKILL.md` — state başlatma
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
