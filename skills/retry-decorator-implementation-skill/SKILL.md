---
name: retry-decorator-implementation
description: Coder AI için — async fonksiyon için yapılandırılabilir retry decorator yazma; exponential backoff, retryable exception filtresi ve max attempt.
---

## Purpose

Retry mantığını tüm LLM ve DB çağrılarında tutarlı hale getirir.
Decorator kullanımı retry kodunun fonksiyon içine dağılmasını önler.
`RetryableError` sınıflandırmasıyla hangi hatanın yeniden deneneceği kontrolü sağlar.

---

## When to Apply

- LLM provider çağrısı yapan fonksiyon retry gerektirdiğinde
- DB operasyonu geçici hata nedeniyle tekrar denenmesi gerektiğinde
- Dış servise HTTP istek yapılan her yerde

---

## Rules

- Decorator sadece `RetryableError` ve alt sınıflarını retry eder.
- `PermanentError` retry yapılmaz — direkt fırlatılır.
- Max attempt: 3 (konfigüre edilebilir).
- Backoff: `2^attempt * base_delay` + jitter.
- Son denemede de başarısız olunca exception fırlatılır.
- Retry sayacı log'a yazılır.

---

## Guidelines

Retry decorator implementasyonu:
```python
import asyncio
import random
import functools
import logging
from typing import Callable, Type

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[Type[Exception], ...] = (RetryableError,)
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(
                            base_delay * (2 ** attempt) + random.uniform(0, 1),
                            max_delay
                        )
                        logger.warning(
                            f"{func.__name__} başarısız (attempt {attempt + 1}/{max_attempts}), "
                            f"{delay:.1f}s sonra yeniden deneniyor: {e}"
                        )
                        await asyncio.sleep(delay)
                except Exception:
                    raise  # PermanentError gibi non-retryable → direkt fırlat
            
            logger.error(f"{func.__name__} {max_attempts} denemeden sonra başarısız")
            raise last_exception
        
        return wrapper
    return decorator


# Kullanım
@async_retry(max_attempts=3, base_delay=2.0)
async def call_llm_provider(prompt: str) -> str:
    response = await provider.generate(prompt)
    return response.text
```

---

## References

- `exponential-backoff-calculation-skill/SKILL.md` — backoff
- `custom-exception-hierarchy-skill/SKILL.md` — exception sınıfları
- `rate-limit-handling-skill/SKILL.md` — rate limit
