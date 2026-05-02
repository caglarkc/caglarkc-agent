---
name: error-categorization
description: Coder AI için — oluşan hataları sistematik kategorilere ayırmak; her kategori için farklı tepki stratejisi uygulamak.
---

## Purpose

Tüm hatalar aynı şekilde işlenmez — bazıları retry, bazıları alert gerektirir.
Kategorizasyon doğru tepkiyi otomatik seçer.
Log analizi ve monitoring için hatalar etiketlenir.

---

## When to Apply

- Global exception handler yazılırken
- Hata loglama standartları belirlenirken
- Worker veya node hata yönetimi implemente edilirken

---

## Rules

- Her hata kategorisi: severity + action + retry_eligible.
- Bilinmeyen hata: `UNKNOWN` kategorisi + alert.
- Kullanıcıya gösterilen mesaj: teknik detay değil, anlaşılır açıklama.
- Hata kategorisi Decision tablosuna değil, log'a yazılır.

---

## Guidelines

```python
from dataclasses import dataclass
from enum import Enum

class ErrorCategory(str, Enum):
    TRANSIENT     = "transient"      # Geçici, retry
    PROVIDER      = "provider"       # LLM provider hatası
    AUTH          = "auth"           # Kimlik doğrulama
    VALIDATION    = "validation"     # Geçersiz input
    FILESYSTEM    = "filesystem"     # Dosya işlem hatası
    DB            = "db"             # Veritabanı hatası
    TIMEOUT       = "timeout"        # Zaman aşımı
    UNKNOWN       = "unknown"        # Bilinmeyen

@dataclass
class CategorizedError:
    category: ErrorCategory
    original: Exception
    retry_eligible: bool
    user_message: str

def categorize_error(exc: Exception) -> CategorizedError:
    if isinstance(exc, asyncio.TimeoutError):
        return CategorizedError(
            category=ErrorCategory.TIMEOUT,
            original=exc,
            retry_eligible=True,
            user_message="İşlem zaman aşımına uğradı, yeniden deneniyor...",
        )
    elif isinstance(exc, (ConnectionError, aiohttp.ClientError)):
        return CategorizedError(
            category=ErrorCategory.TRANSIENT,
            original=exc,
            retry_eligible=True,
            user_message="Bağlantı hatası, yeniden deneniyor...",
        )
    elif isinstance(exc, PermissionError):
        return CategorizedError(
            category=ErrorCategory.AUTH,
            original=exc,
            retry_eligible=False,
            user_message="Yetki hatası — yapılandırmayı kontrol edin.",
        )
    elif isinstance(exc, (OSError, IOError)):
        return CategorizedError(
            category=ErrorCategory.FILESYSTEM,
            original=exc,
            retry_eligible=False,
            user_message=f"Dosya işlem hatası: {exc}",
        )
    else:
        return CategorizedError(
            category=ErrorCategory.UNKNOWN,
            original=exc,
            retry_eligible=False,
            user_message="Beklenmedik hata oluştu.",
        )
```

---

## References

- `retry-decision-logic-skill/SKILL.md` — retry kararı
- `cascading-failure-prevention-skill/SKILL.md` — yayılma önleme
- `logging-patterns-skill/SKILL.md` — hata loglama
