---
name: sprint-dependency-management
description: Planner AI için — sprint'ler arası bağımlılıkları yönetmek; Sprint 2'nin Sprint 1'in sonuçlarına bağlı olduğunu kullanıcıya açıklamak.
---

## Purpose

Sprint 2'deki repository kodu Sprint 1'de yazılan models.py'e bağlıdır.
Bağımlılık bilinmezse sprint yanlış sırayla başlatılır.
PM, sprint bağımlılıklarını açıkça kullanıcıya bildirir.

---

## When to Apply

- Multi-sprint roadmap planlanırken
- Yeni sprint planlanmadan önce önceki sprint tamamlanmış mı kontrolünde
- Bağımlı sprint başlatılmak istendiğinde öncekinin durumu kontrol edilirken

---

## Rules

- Sprint bağımlılığı: `depends_on_sprint_id` alanı.
- Bağımlı sprint tamamlanmadan yeni sprint başlatılmaz.
- Kullanıcı zorunlu yaparsa uyarı verilir, onaylanırsa devam edilir.
- Bağımlılıklar DB'ye kayıt edilir.

---

## Guidelines

```python
async def check_sprint_dependency(
    sprint_id: str,
    depends_on: str | None,
    repo: ProjectRepository,
) -> tuple[bool, str]:
    """Returns (can_start, reason)."""
    if not depends_on:
        return True, ""
    
    dependency = await repo.get_sprint(depends_on)
    if not dependency:
        return False, f"Bağımlı sprint bulunamadı: {depends_on}"
    
    if dependency.status != "done":
        return False, (
            f"Sprint {sprint_id} başlamadan önce "
            f"Sprint {depends_on} tamamlanmalı "
            f"(mevcut durum: {dependency.status})"
        )
    
    return True, ""

async def validate_sprint_chain(
    sprints: list[dict],
    repo: ProjectRepository,
) -> list[str]:
    """Sprint zincirindeki bağımlılık ihlallerini döndürür."""
    errors = []
    for sprint in sprints:
        can_start, reason = await check_sprint_dependency(
            sprint["sprint_id"],
            sprint.get("depends_on"),
            repo,
        )
        if not can_start:
            errors.append(reason)
    return errors
```

PM mesaj formatı:
```
[PLANLAMA] Bağımlılık uyarısı!

Sprint 3 başlatılamıyor:
  → Sprint 2 henüz tamamlanmadı (durum: active)

Sprint 2'nin tamamlanmasını bekleyin veya bağımlılığı 
kaldırmak ister misiniz? (önerilmez)
```

---

## References

- `task-dependency-ordering-skill/SKILL.md` — görev bağımlılığı
- `multi-sprint-roadmap-design-skill/SKILL.md` — roadmap
- `sprint-lifecycle-state-machine-skill/SKILL.md` — sprint durumu
