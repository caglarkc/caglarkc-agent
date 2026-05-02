---
name: user-feedback-collection
description: Planner AI için — sprint tamamlandıktan sonra kullanıcıdan kalite geri bildirimi almak; gelecek sprint'leri iyileştirmek için.
---

## Purpose

Kullanıcı memnuniyeti ölçülmezse iyileştirme fırsatları kaçırılır.
Kısa sprint sonu anketi bağlam kesimine neden olmaz.
Geri bildirim Decision tablosuna kaydedilir.

---

## When to Apply

- Sprint `done` durumuna geçtiğinde
- Uzun veya karmaşık sprint tamamlandığında
- Kullanıcı kendi isteğiyle geri bildirim verdiğinde

---

## Rules

- Geri bildirim opsiyoneldir — zorunlu tutulmaz.
- Maksimum 2 soru — uzun anket yapılmaz.
- Cevap kısa format: "iyi/orta/kötü" veya 1-5 puan.
- Kaydedilen geri bildirim: Decision tablosuna `"feedback"` tipiyle.

---

## Guidelines

PM geri bildirim sorusu:
```
[SOHBET] Sprint 3 tamamlandı!

Üretilen kod kalitesini değerlendirir misiniz?
(1-5 veya atlamak için "geç" yazın)

1 — Kullanılamaz
2 — Önemli düzeltmeler gerekli
3 — Kabul edilebilir, küçük düzeltmeler
4 — İyi
5 — Mükemmel
```

```python
async def collect_sprint_feedback(
    project_id: str,
    sprint_id: str,
    user_rating: str | None,
    user_comment: str | None,
    repo: ProjectRepository,
) -> None:
    if not user_rating or user_rating.lower() in ("geç", "atla", "skip"):
        return
    
    await repo.create_decision(Decision(
        project_id=project_id,
        sprint_id=sprint_id,
        summary=f"Sprint {sprint_id} geri bildirimi: {user_rating}/5",
        rationale=(
            f"Kullanıcı puanı: {user_rating}\n"
            f"Yorum: {user_comment or 'Yok'}"
        ),
        decision_type="feedback",
    ))
    
    logger.info(f"Geri bildirim kaydedildi: {sprint_id} → {user_rating}")
```

---

## References

- `sprint-completion-celebration-skill/SKILL.md` — tamamlanma mesajı
- `decision-log-maintenance-skill/SKILL.md` — kayıt
- `pm-mode-skill/SKILL.md` — PM modları
