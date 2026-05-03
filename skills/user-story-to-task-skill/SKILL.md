---
name: user-story-to-task
description: Planner AI için — kullanıcı hikayesini ("Kullanıcı olarak X yapabilmek istiyorum") teknik görevlere dönüştürmek.
---

## Purpose

Kullanıcı hikayesi isteği anlatır; teknik görev ne yapılacağını söyler.
"Login olmak istiyorum" → JWT + user model + endpoint + test görevleri.
PM bu dönüşümü yapar kullanıcı onayına sunar.

---

## When to Apply

- Kullanıcı isteklerini "Kullanıcı olarak..." formatıyla ifade ettiğinde
- Product owner gibi düşünen bir arayüz tasarlanırken
- Agile user story formatından teknik sprint oluşturulurken

---

## Rules

- Her user story: 3-7 teknik göreve dönüştürülür.
- Göreve acceptance criteria eklenir.
- Teknik olmayan kullanıcı için PM hikayeyi özetler.
- Bir hikayeden birden fazla sprint oluşabilir.

---

## Guidelines

User story analizi:
```
Hikaye: "Kullanıcı olarak sprint tarihçesini görmek istiyorum"

Teknik görevler:
1. SprintHistory sorgu metodu (repository.py)
2. sprint-history CLI komutu (commands.py)
3. Sprint tarihçesi Telegram komutu (/history)
4. Tarihçe formatı (utils/formatting.py)
5. Testler (test_sprint_history.py)

Kabul kriterleri:
- Son 5 sprint listelenir
- Her sprint: ID, tarih, durum, dosya sayısı
- Telegram ve CLI'da çalışır
```

```python
def parse_user_story(story: str) -> dict:
    """User story'den bileşenleri çıkarır."""
    import re
    
    # "Kullanıcı olarak X yapabilmek istiyorum, böylece Y"
    match = re.match(
        r"(?:kullanıcı olarak\s+)?(.+?)\s+(?:yapabilmek\s+)?istiyorum"
        r"(?:,\s*böylece\s+(.+))?",
        story.lower()
    )
    
    if match:
        return {
            "action": match.group(1).strip(),
            "benefit": match.group(2).strip() if match.group(2) else "",
        }
    
    return {"action": story, "benefit": ""}
```

---

## References

- `user-story-decomposition-skill/SKILL.md` — story ayrıştırma
- `acceptance-criteria-definition-skill/SKILL.md` — kabul kriterleri
- `sprint-task-decomposition-skill/SKILL.md` — görev ayrıştırma
