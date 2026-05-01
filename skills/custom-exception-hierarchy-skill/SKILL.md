---
name: custom-exception-hierarchy
description: Coder AI için — bu projeye özgü exception sınıf hiyerarşisini tasarlamak ve uygulamak; hatanın kaynağına göre spesifik exception tipleri kullanmak.
---

## Purpose

Hataları tipine göre ayırt etmeyi sağlar.
`except Exception` yerine `except LLMTimeoutError` gibi spesifik yakalama yapılabilir.
Retryable / non-retryable ayrımı exception tipinden anlaşılır.

---

## When to Apply

- Yeni hata kaynağı (servis, entegrasyon) ekleneceğinde
- `WorkerFailureLog.retryable` belirlenirken
- Retry decorator hangi exception'ı yakalayacak karar verilirken

---

## Rules

- Tüm proje exception'ları `OrchestratorError`'dan türer.
- Retryable exception'lar `RetryableError`'dan türer.
- Non-retryable exception'lar `PermanentError`'dan türer.
- Exception mesajları kullanıcıya gösterilecekse Türkçe olabilir.
- Exception chaining zorunlu: `raise NewError("msg") from original`.

---

## Guidelines

Exception hiyerarşisi:
```python
# src/core/exceptions.py

class OrchestratorError(Exception):
    """Tüm orchestrator hatalarının base class'ı."""
    pass


# Retryable hatalar
class RetryableError(OrchestratorError):
    """Yeniden deneme yapılabilecek hatalar."""
    pass

class LLMTimeoutError(RetryableError):
    """LLM provider yanıt vermedi."""
    pass

class RateLimitError(RetryableError):
    """API rate limit aşıldı."""
    pass

class ProviderConnectionError(RetryableError):
    """Provider'a bağlanılamadı."""
    pass


# Kalıcı hatalar
class PermanentError(OrchestratorError):
    """Retry faydasız, müdahale gerekiyor."""
    pass

class InvalidTaskError(PermanentError):
    """Görev açıklaması geçersiz."""
    pass

class FilePermissionError(PermanentError):
    """Dosyaya yazma izni yok."""
    pass

class StateCorruptionError(PermanentError):
    """State bütünlüğü bozuldu."""
    pass


# Özel hatalar
class ApprovalTimeoutError(OrchestratorError):
    """Onay süresi doldu."""
    pass

class CircularDependencyError(OrchestratorError):
    """Bağımlılık döngüsü tespit edildi."""
    pass
```

Kullanım:
```python
try:
    response = await llm_client.generate(prompt, timeout=30)
except httpx.TimeoutException as e:
    raise LLMTimeoutError(f"LLM {timeout}s içinde yanıt vermedi") from e
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        raise RateLimitError("Rate limit") from e
    raise PermanentError(f"HTTP {e.response.status_code}") from e
```

---

## References

- `exception-handling-review-skill/SKILL.md` — hata handling review
- `retry-decorator-implementation-skill/SKILL.md` — retry mantığı
- `worker-failure-triage-skill/SKILL.md` — hata sınıflandırma
