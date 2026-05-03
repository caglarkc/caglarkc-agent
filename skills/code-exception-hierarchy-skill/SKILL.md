---
name: code-exception-hierarchy
description: Coder AI için — proje özel istisna hiyerarşisi tasarlamak; hataları kategorize etmek ve tutarlı yakalamayı sağlamak.
---

## Purpose

Tüm hataları `Exception` olarak fırlatmak yakalamayı zorlaştırır.
Özel istisna hiyerarşisi: hata türünü anlamlı yapar, `except` ifadeleri hedefli olur.
Sprint sistemi için: LLM hatası, DB hatası, validation hatası ayrı sınıflar.

---

## When to Apply

- Yeni servis modülü tasarlanırken
- `raise Exception("hata")` yerine anlamlı hata fırlatılmak istendiğinde
- Hata yakalama mantığı `except Exception` yerine spesifik olacaksa

---

## Rules

- Taban: `AgentError(Exception)` — tüm sistem hataları buradan.
- Alt sınıflar: LLMError, DBError, ValidationError, WorkerError.
- Mesaj: `str(exc)` ile okunabilir olmalı.
- Gizli bilgi: API key, token hata mesajına yazılmaz.

---

## Guidelines

```python
class AgentError(Exception):
    """Tüm ajan sistemi hatalarının tabanı."""
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code

class LLMError(AgentError):
    """LLM sağlayıcı hatası."""

class LLMTimeoutError(LLMError):
    """LLM zaman aşımına uğradı."""

class LLMRateLimitError(LLMError):
    """LLM hız limiti aşıldı."""

class DBError(AgentError):
    """Veritabanı hatası."""

class DBConnectionError(DBError):
    """DB bağlantısı kurulamadı."""

class ValidationError(AgentError):
    """Üretilen kod veya plan doğrulanamadı."""

class WorkerError(AgentError):
    """Worker yürütme hatası."""

class WorkerTimeoutError(WorkerError):
    """Worker zaman aşımına uğradı."""

# Kullanım
def categorize_exception(exc: Exception) -> str:
    if isinstance(exc, LLMTimeoutError):
        return "llm_timeout"
    elif isinstance(exc, LLMRateLimitError):
        return "llm_rate_limit"
    elif isinstance(exc, LLMError):
        return "llm_error"
    elif isinstance(exc, DBError):
        return "db_error"
    elif isinstance(exc, ValidationError):
        return "validation_error"
    elif isinstance(exc, WorkerError):
        return "worker_error"
    elif isinstance(exc, AgentError):
        return "agent_error"
    return "unknown"
```

---

## References

- `error-categorization-skill/SKILL.md` — hata kategorileme
- `node-error-boundary-skill/SKILL.md` — node hata sınırı
- `retry-decision-logic-skill/SKILL.md` — retry kararı
