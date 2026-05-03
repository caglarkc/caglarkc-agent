---
name: sprint-cancellation
description: Planner AI için — aktif sprint'in kullanıcı isteğiyle veya hata durumunda iptal edilmesi; kaynakların temizlenmesi ve durumun kaydedilmesi.
---

## Purpose

Kullanıcı "iptal et" diyebilir veya kritik hata sprint'i durdurmayı gerektirir.
İptal edilen sprint temiz bir şekilde kapatılmalı — orphan worker olmaz.
İptal kararı Decision tablosuna yazılır.

---

## When to Apply

- Kullanıcı "sprint iptal" veya "dur" komutu verdiğinde
- Kritik hata sprint devam edemeyeceğini gösterdiğinde
- Timeout sonrası otomatik iptal yapılırken

---

## Rules

- İptal: `ACTIVE → CANCELLED` geçişi.
- Aktif worker'lara shutdown sinyali gönderilir.
- `in_progress` dosyalar `planned`'a alınmaz — `failed` yapılır.
- İptal kararı Decision olarak kaydedilir.
- Sonraki sprint yeni başlangıçla açılabilir.

---

## Guidelines

```python
async def cancel_sprint(
    project_id: str,
    sprint_id: str,
    reason: str,
    repo: ProjectRepository,
    compiled_graph,
) -> None:
    logger.info(f"Sprint iptal ediliyor: {sprint_id}, sebep: {reason}")
    
    # State'i güncelle
    config = get_thread_config(project_id)
    snapshot = await compiled_graph.aget_state(config=config)
    current = snapshot.values
    
    # Aktif işleri fail yap
    registry = dict(current.get("file_registry", {}))
    updated_registry = {
        path: "failed" if status in ("in_progress", "reserved") else status
        for path, status in registry.items()
    }
    
    await compiled_graph.aupdate_state(
        config=config,
        values={
            "file_registry": updated_registry,
            "sprint_status": "cancelled",
        }
    )
    
    # DB'de sprint durumunu güncelle
    await repo.update_sprint_status(sprint_id, "cancelled")
    
    # Karar kaydet
    await repo.create_decision(Decision(
        project_id=project_id,
        sprint_id=sprint_id,
        summary=f"Sprint {sprint_id} iptal edildi",
        rationale=f"Sebep: {reason}",
        decision_type="cancellation",
    ))
```

PM mesaj formatı:
```
[SOHBET] Sprint iptal edildi.

Sebep: Kullanıcı isteği
Durum: İptal sırasında çalışan 2 görev durduruldu.

Yeni sprint başlatmak ister misiniz?
```

---

## References

- `sprint-lifecycle-state-machine-skill/SKILL.md` — durum geçişi
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
- `graceful-shutdown-implementation-skill/SKILL.md` — shutdown
