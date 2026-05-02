---
name: user-intent-clarification
description: Planner AI için — kullanıcının ne istediği net olmadığında doğru soruyu sormak; tek soru ile maksimum bilgi toplamak.
---

## Purpose

Yanlış anlaşılan istek yanlış sprint planı üretir.
Bir netleştirme sorusu çok sayıda varsayımı ortadan kaldırır.
İyi soru: kapalı uçlu (evet/hayır) değil, açık uçlu.

---

## When to Apply

- Kullanıcı isteği birden fazla yoruma açık olduğunda
- Teknik detay eksikse (hangi model? hangi arayüz?)
- "Hem A hem B" mi, "sadece A" mı belirsizken

---

## Rules

- En fazla 2 netleştirme sorusu — daha fazlası kullanıcıyı yorar.
- Soru: somut, yanıtlanabilir.
- Varsayım yapmak mümkünse: varsayımı belirt, sor.
- "Bilmiyorum" kabul edilir — konuşmaya devam et.

---

## Guidelines

```python
def needs_clarification(user_message: str) -> bool:
    """Netleştirme gerekip gerekmediğini kontrol et."""
    vague_indicators = [
        len(user_message.split()) < 5,      # çok kısa
        "?" not in user_message and          # soru değil
        "!" not in user_message and
        all(
            kw not in user_message.lower()
            for kw in ["ekle", "yaz", "oluştur", "test", "düzelt"]
        ),
    ]
    return any(vague_indicators)

def build_clarification_question(user_message: str) -> str:
    """İsteğe göre netleştirme sorusu oluştur."""
    msg_lower = user_message.lower()
    
    if "telegram" in msg_lower and "bot" not in msg_lower:
        return (
            "Telegram entegrasyonunu hangi kapsamda istiyorsunuz?\n"
            "a) Sadece bildirim gönderme\n"
            "b) Onay/ret komutu alma\n"
            "c) Her ikisi"
        )
    
    if "api" in msg_lower and "rest" not in msg_lower and "fastapi" not in msg_lower:
        return "Hangi API framework'ünü kullanmak istiyorsunuz? (FastAPI, Flask, vb.)"
    
    return (
        f"İsteğinizi biraz daha açar mısınız?\n"
        f"Özellikle: hangi dosya veya modül etkilenecek?"
    )
```

PM formatı:
```
[SOHBET] İsteğinizi anlamak için bir soru:

"API ekle" derken ne kastediyorsunuz?

a) Mevcut CLI'ya yeni komut ekle
b) REST API endpoint'i oluştur (FastAPI)
c) LLM API entegrasyonu

(varsayımım: b — FastAPI endpoint, doğru mu?)
```

---

## References

- `vague-requirement-clarification-skill/SKILL.md` — belirsizlik
- `implicit-assumption-surfacing-skill/SKILL.md` — varsayım
- `pm-mode-skill/SKILL.md` — PM modları
