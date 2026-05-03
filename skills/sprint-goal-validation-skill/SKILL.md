---
name: sprint-goal-validation
description: Planner AI için — sprint hedefinin somut, ölçülebilir ve tek sprint'e sığar olduğunu doğrulamak; belirsiz hedefleri reddetmek.
---

## Purpose

"Her şeyi iyileştir" gibi belirsiz hedef planlanamaz.
SMART kriterleri (Specific, Measurable, Achievable) kontrol edilir.
Geçersiz hedef netleştirme sorusu ile geri döndürülür.

---

## When to Apply

- Kullanıcı sprint hedefi söylediğinde
- Plan oluşturulmadan önce hedef doğrulama aşamasında
- Çok büyük veya çok belirsiz istek alındığında

---

## Rules

- Hedef: en az 10 karakter, en fazla 200 karakter.
- Hedef: somut bir çıktı içermeli ("ekle", "yaz", "oluştur").
- Hedef: mevcut sprint kapsamına sığmalı (max 8 görev).
- Belirsiz hedef: açıklama sorusuyla geri döndürülür.
- Kabul edilmiş hedef değiştirilmez — yeni sprint açılır.

---

## Guidelines

```python
VAGUE_PATTERNS = [
    "iyileştir", "düzelt", "refactor et", "temizle",
    "her şeyi", "tüm", "genel", "genel olarak",
]

ACTIONABLE_KEYWORDS = [
    "ekle", "oluştur", "yaz", "implement et", "entegre et",
    "kaldır", "güncelle", "değiştir", "test et",
]

def validate_sprint_goal(goal: str) -> tuple[bool, str]:
    """Returns (is_valid, feedback_message)."""
    if len(goal.strip()) < 10:
        return False, "Hedef çok kısa. Daha spesifik olun."
    
    goal_lower = goal.lower()
    
    has_vague = any(p in goal_lower for p in VAGUE_PATTERNS)
    has_action = any(k in goal_lower for k in ACTIONABLE_KEYWORDS)
    
    if has_vague and not has_action:
        return False, (
            "Hedef çok belirsiz. Hangi spesifik özelliği ekleyeceğiz?\n"
            "Örnek: 'Telegram onay bildirimini ekle' veya "
            "'Repository katmanını test et'"
        )
    
    if len(goal) > 200:
        return False, "Hedef çok uzun. Tek cümleyle özetleyin."
    
    return True, ""
```

PM doğrulama mesajı:
```
[SOHBET] Hedef netleştirmesi gerekiyor.

"Her şeyi iyileştir" ile ne demek istiyorsunuz?

Örnekler:
- "Planner node'un hata yönetimini düzelt"
- "Worker retry mekanizmasını ekle"
- "Repository testleri yaz"
```

---

## References

- `vague-requirement-clarification-skill/SKILL.md` — belirsizlik
- `sprint-goal-articulation-skill/SKILL.md` — hedef belirleme
- `scope-boundary-detection-skill/SKILL.md` — kapsam
