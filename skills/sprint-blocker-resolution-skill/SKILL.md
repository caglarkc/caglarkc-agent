---
name: sprint-blocker-resolution
description: Planner AI için — sprint'i engelleyen teknik veya organizasyonel blocker'ları tespit etmek ve çözüm önerileri sunmak.
---

## Purpose

Sprint ilerlemiyor ama neden net değil — blocker tespiti gerekli.
Teknik blocker: eksik bağımlılık, environment sorunu, test başarısızlığı.
Organizasyonel blocker: onay eksikliği, bilgi eksikliği.

---

## When to Apply

- Sprint taktığında ve ilerlemediğinde
- Aynı hata birden fazla kez görüldüğünde
- Kullanıcı "neden bitmiyor?" diye sorduğunda

---

## Rules

- Blocker: sprint'in devam etmesini engelleyen her şey.
- Blocker kategorize edilir: teknik, environment, bilgi, onay.
- Her blocker için çözüm önerisi sunulur.
- Kullanıcı müdahalesi gerektiren blocker'lar özellikle belirtilir.

---

## Guidelines

```python
from enum import Enum

class BlockerCategory(str, Enum):
    TECHNICAL    = "technical"      # Kod hatası, bağımlılık
    ENVIRONMENT  = "environment"    # Konfigürasyon, API key
    KNOWLEDGE    = "knowledge"      # Bilgi eksikliği
    APPROVAL     = "approval"       # Onay bekleniyor
    EXTERNAL     = "external"       # LLM provider, network

def categorize_blocker(error_message: str) -> BlockerCategory:
    msg_lower = error_message.lower()
    
    if any(k in msg_lower for k in ["import", "module", "syntax"]):
        return BlockerCategory.TECHNICAL
    elif any(k in msg_lower for k in ["api key", "token", "unauthorized", "403"]):
        return BlockerCategory.ENVIRONMENT
    elif any(k in msg_lower for k in ["timeout", "connection", "502", "503"]):
        return BlockerCategory.EXTERNAL
    elif "approval" in msg_lower or "onay" in msg_lower:
        return BlockerCategory.APPROVAL
    else:
        return BlockerCategory.KNOWLEDGE

RESOLUTION_TEMPLATES = {
    BlockerCategory.TECHNICAL: "Kod hatası — görev yeniden planlanacak",
    BlockerCategory.ENVIRONMENT: "Konfigürasyon sorunu — .env kontrol edilmeli",
    BlockerCategory.EXTERNAL: "Provider sorunu — fallback deneniyor",
    BlockerCategory.APPROVAL: "Onay bekleniyor — kullanıcı müdahalesi gerekli",
    BlockerCategory.KNOWLEDGE: "Bilgi eksik — kullanıcıdan clarification isteniyor",
}
```

PM mesaj formatı:
```
[SOHBET] Sprint blocker tespit edildi:

Kategori: Environment
Hata: GEMINI_API_KEY geçersiz veya eksik

Çözüm önerileri:
1. .env dosyasındaki GEMINI_API_KEY değerini kontrol edin
2. API key'in aktif olduğunu Google Cloud Console'dan doğrulayın
3. Alternatif: Ollama provider'ına geçin

Hazır olduğunuzda devam edebiliriz.
```

---

## References

- `cascading-failure-prevention-skill/SKILL.md` — hata yayılması
- `error-categorization-skill/SKILL.md` — hata kategorisi
- `stall-detection-response-skill/SKILL.md` — takılma tespiti
