---
name: stall-detection-response
description: Planner AI için — sistemin takılı kaldığını (heartbeat gelmiyor, progress yok) tespit etmek ve uygun aksiyonu almak.
---

## Purpose

Graph'ın sessizce takılı kaldığı durumları tespit eder.
600 saniye (10 dakika) heartbeat gelmezse sistem stall'da sayılır.
Stall'dan kurtarma: resume, restart, veya kullanıcı bildirimi.

---

## When to Apply

- `system.heartbeat` event'i beklenen sürede gelmediğinde
- `system.stalled` event'i alındığında
- Worker uzun süredir `in_progress` durumunda beklenirken
- Daemon monitoring sırasında

---

## Rules

- Stall eşiği: 600 saniye heartbeat yok = stall.
- İlk tepki: checkpoint'ten resume dene.
- Resume başarısız: kullanıcıya bildir.
- Kullanıcı bildiriminde hangi proje, ne kadar süredir bekliyor bilgisi verilir.
- Stall sonrası resume başarılıysa `system.recovered` emit edilir.
- LLM provider timeout ayrıca: 30 saniye yanıt yok → timeout, retry.

---

## Guidelines

Stall tespit mantığı:
```python
STALL_TIMEOUT = 600  # saniye

async def check_stall():
    last_heartbeat = state_manager.get_last_heartbeat(project_id)
    elapsed = (datetime.utcnow() - last_heartbeat).total_seconds()
    
    if elapsed > STALL_TIMEOUT:
        await event_bus.emit("system.stalled", {
            "project_id": project_id,
            "elapsed_seconds": elapsed,
            "last_node": state.get("current_node")
        })
```

Stall'dan kurtarma akışı:
```
system.stalled alındı:
1. Thread'i checkpoint'ten resume dene
   → Başarılı: system.recovered emit et, devam
   → Başarısız:
2. Kullanıcıya bildir:
   "[project_X] 10 dakikadır ilerlem yok.
    Worker durumu: in_progress (planner.py)
    /resume komutuyla devam edebilirsiniz."
3. Thread'i dondur (cancel etme, sadece bekle)
```

Farklı stall türleri:
```
LLM stall: provider yanıt vermiyor → timeout → retry
Worker stall: worker assigned ama progress yok → farklı worker
Graph stall: node tamamlandı ama edge routing çalışmadı → inspect state
Approval stall: onay bekleniyor, süre doldu → kullanıcıya bildir
```

---

## References

- `heartbeat-emission-skill/SKILL.md` — heartbeat gönderme
- `partial-sprint-recovery-skill/SKILL.md` — kısmi recovery
- `checkpoint-strategy-review-skill/SKILL.md` — checkpoint resume
