---
name: rollback-strategy
description: Planner AI için — başarısız sprint sonrası yazılan dosyaların geri alınmasını planlamak; sistemin önceki çalışan durumuna dönmesini sağlamak.
---

## Purpose

Sprint başarısız olursa yarım yazılan dosyalar sistemi bozabilir.
Rollback önceki çalışan versiyona güvenle dönmeyi sağlar.
Her rollback kararı kayıt altına alınır.

---

## When to Apply

- Sprint `failed` veya `cancelled` durumuna geçtiğinde
- Reviewer kritik hatalar bulduğunda
- Kullanıcı "geri al" dediğinde

---

## Rules

- Rollback: sadece sprint kapsamındaki dosyalara uygulanır.
- Eski versiyon git history'den geri yüklenir (tercih).
- Git yoksa: backup stratejisi gerekir.
- Rollback sonrası Decision kaydı oluşturulur.
- Kısmi rollback mümkün: sadece başarısız dosyalar.

---

## Guidelines

```python
async def plan_rollback(
    sprint_id: str,
    file_registry: dict[str, str],
    strategy: str = "git"
) -> RollbackPlan:
    failed_files = [
        p for p, s in file_registry.items()
        if s == "failed"
    ]
    done_files = [
        p for p, s in file_registry.items()
        if s == "done"
    ]
    
    return RollbackPlan(
        sprint_id=sprint_id,
        files_to_rollback=done_files,  # başarıyla yazılanlar geri alınır
        files_to_remove=failed_files,  # başarısızlar silinir
        strategy=strategy,
    )

async def execute_git_rollback(
    files: list[str],
    before_commit: str,
) -> None:
    for file_path in files:
        try:
            await run_command([
                "git", "checkout", before_commit, "--", file_path
            ])
            logger.info(f"Rollback: {file_path}")
        except SubprocessError as e:
            logger.error(f"Rollback başarısız: {file_path}: {e}")
```

PM mesaj formatı:
```
[PLANLAMA] Rollback seçenekleri:

Sprint 3 başarısız oldu. 3 dosya yazıldı, 2 başarısız.

Seçenek 1: Tüm sprint'i geri al (3+2 dosya)
Seçenek 2: Sadece başarısız dosyaları temizle (2 dosya)
Seçenek 3: Mevcut haliyle devam et

Ne yapalım?
```

---

## References

- `sprint-cancellation-skill/SKILL.md` — sprint iptali
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
- `subprocess-async-skill/SKILL.md` — git komutu
