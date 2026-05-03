---
name: progress-report-generation
description: Planner AI için — sprint boyunca tamamlanan ve bekleyen görevlerin özetini çıkarmak; kullanıcıya net ilerleme raporu sunmak.
---

## Purpose

Kullanıcı "ne kadar bitti?" diye sorduğunda hazır cevap verir.
Sprint state'inden otomatik istatistik çeker.
File registry ve task listesinden gerçek ilerleme hesaplanır.

---

## When to Apply

- Kullanıcı ilerleme sorarken
- Sprint uzun sürüyorsa durum güncellemesi gerektiğinde
- Review öncesi özet sunulurken
- HITL onay beklerken ara rapor hazırlanırken

---

## Rules

- `done` dosya sayısı / toplam dosya = yüzde hesaplanır.
- `failed` dosyalar ayrıca belirtilir.
- Tahmini kalan süre hesaplanmaz — sadece mevcut durum.
- Her sprint için ayrı rapor; önceki sprint karıştırılmaz.

---

## Guidelines

Progress hesaplama:
```python
async def generate_progress_report(
    state: OrchestratorState
) -> str:
    file_registry = state.get("file_registry", {})
    tasks = state.get("tasks", [])
    
    total = len(file_registry)
    done = sum(1 for s in file_registry.values() if s == "done")
    in_progress = sum(1 for s in file_registry.values() if s == "in_progress")
    failed = sum(1 for s in file_registry.values() if s == "failed")
    pending = total - done - in_progress - failed
    
    pct = (done / total * 100) if total > 0 else 0
    
    task_done = sum(1 for t in tasks if t.get("status") == "done")
    task_total = len(tasks)
    
    return (
        f"SPRINT İLERLEME RAPORU\n"
        f"{'='*30}\n"
        f"Dosyalar: {done}/{total} tamamlandı ({pct:.0f}%)\n"
        f"  ✓ Tamamlandı: {done}\n"
        f"  ⟳ Devam ediyor: {in_progress}\n"
        f"  ✗ Başarısız: {failed}\n"
        f"  ○ Bekliyor: {pending}\n\n"
        f"Görevler: {task_done}/{task_total} tamamlandı\n"
    )
```

PM rapor formatı:
```
[SOHBET] Sprint 3 ilerleme durumu:

Dosyalar: 8/12 tamamlandı (%67)
  ✓ 8 dosya yazıldı
  ⟳ 2 devam ediyor
  ○ 2 bekliyor

Görevler: 5/7 tamamlandı
Tahmini kalan: 2-3 görev daha
```

---

## References

- `sprint-completion-validation-skill/SKILL.md` — tamamlanma doğrulama
- `file-status-state-machine-skill/SKILL.md` — dosya durum
- `worker-status-tracking-skill/SKILL.md` — worker durumu
