---
name: code-decorator-factory
description: Coder AI için — parametreli decorator (decorator factory) yazmak; retry, timeout, cache gibi davranışları fonksiyonlara dinamik eklemek.
---

## Purpose

Tekrar eden cross-cutting concern'ler (retry, log, cache) her fonksiyona elle eklenmez.
Decorator factory: parametreli, yeniden kullanılabilir davranış sarmalayıcı üretir.
`@retry(max=3)` gibi temiz, açıklayıcı API sağlar.

---

## When to Apply

- Retry, timeout, cache gibi davranış birden fazla fonksiyona eklenirken
- Fonksiyon imzasını değiştirmeden davranış enjekte edilirken
- AOP (Aspect-Oriented) yaklaşımı benimsenirken

---

## Rules

- `functools.wraps`: orijinal fonksiyonun meta bilgisini koru.
- Async: async fonksiyon için ayrı wrapper.
- Hata: decorator hatası sarmaladığı fonksiyonu çökertemez.
- Test: decorator davranışı bağımsız test edilebilir.

---

## Guidelines

```python
import asyncio
import functools
import logging
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)
logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        await asyncio.sleep(delay * attempt)
            raise last_exc

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            import time
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)
            raise last_exc

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper
    return decorator

def log_call(logger_name: str = __name__):
    def decorator(fn: F) -> F:
        _logger = logging.getLogger(logger_name)
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            _logger.debug("Çağrılıyor: %s", fn.__name__)
            result = await fn(*args, **kwargs)
            _logger.debug("Tamamlandı: %s", fn.__name__)
            return result
        return wrapper
    return decorator

# Kullanım
@retry(max_attempts=3, delay=2.0, exceptions=(TimeoutError,))
@log_call("sprint.worker")
async def call_llm(messages: list) -> str:
    ...
```

---

## References

- `retry-decision-logic-skill/SKILL.md` — retry kararı
- `async-timeout-pattern-skill/SKILL.md` — async timeout
- `logging-patterns-skill/SKILL.md` — loglama kalıpları
