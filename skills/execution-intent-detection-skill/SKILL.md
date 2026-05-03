---
name: execution-intent-detection
description: Planner AI için — kullanıcının sadece tartışmak mı yoksa gerçekten kodu çalıştırmak mı istediğini tespit etmek; yanlış execution intent tespiti gereksiz sprint başlatır.
---

## Purpose

Kullanıcı mesajından "hemen yap" ile "konuşalım/sormak istiyorum" arasındaki farkı yakalar.
Yanlış tespit: tartışma istiyorken sprint başlatmak kullanıcıyı şaşırtır.
Doğru tespit: gerçek iş isteğini hemen planlama moduna alır.

---

## When to Apply

- Her yeni kullanıcı mesajı alındığında
- `execution_intent` alanı set edilmeden önce
- Manager planning service'in `process_turn()` çağrısında

---

## Rules

- Execution intent sinyalleri: "yap", "ekle", "yaz", "oluştur", "implement et", "kodu yaz", "başlat".
- Tartışma sinyalleri: "nasıl yaparız?", "ne düşünüyorsun?", "mümkün mü?", "fikrin nedir?".
- Belirsiz durumda: `[SOHBET]` modunda sor — asla otomatik sprint başlatma.
- İngilizce kelimeler de kontrol edilmeli: "do it", "implement", "create", "add".
- "Tamam" veya "evet" onay isteğine cevap olabilir → önceki bağlama bakılır.

---

## Guidelines

Intent tespit mantığı:
```python
EXECUTION_KEYWORDS = [
    "yap", "ekle", "yaz", "oluştur", "implement",
    "başlat", "çalıştır", "uygula", "kodu yaz",
    "sprint başlat", "devam et", "do it", "create", "add"
]

DISCUSSION_KEYWORDS = [
    "nasıl", "ne düşünüyorsun", "mümkün mü", "fikrin",
    "anlat", "açıkla", "sormak istiyorum", "how", "what do you think"
]

def detect_intent(message: str) -> str:
    lower = message.lower()
    exec_score = sum(1 for k in EXECUTION_KEYWORDS if k in lower)
    discuss_score = sum(1 for k in DISCUSSION_KEYWORDS if k in lower)
    
    if exec_score > discuss_score:
        return "execution"
    elif discuss_score > 0:
        return "discussion"
    return "unclear"  # → soru sor
```

Onay mesajı özel durumu:
```python
# Kullanıcı "evet" veya "tamam" dedi
if approval_request mevcut:
    → bu bir onay, execution değil
    → plan.approved event emit et
else:
    → bağlam belirsiz, sor
```

---

## References

- `pm-mode-skill/SKILL.md` — mod geçişleri
- `multi-turn-context-preservation-skill/SKILL.md` — bağlam takibi
- `vague-requirement-clarification-skill/SKILL.md` — belirsizlikte soru sor
