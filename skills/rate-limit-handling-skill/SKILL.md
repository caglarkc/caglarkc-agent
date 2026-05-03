---
name: rate-limit-handling
description: Coder AI için — LLM provider'lardan gelen 429 rate limit hatalarını tespit etmek, exponential backoff ile yeniden denemek ve farklı provider'a geçmek.
---

## Purpose

Rate limit hatalarında sistemi bekletip yeniden denemeyi sağlar.
429 yanıtını `RetryableError` olarak sınıflandırır.
`Retry-After` header'ına saygı göstererek akıllı bekleme uygular.

---

## When to Apply

- Herhangi bir LLM provider'a HTTP istek yapılırken
- Provider'dan 429 yanıtı geldiğinde
- Worker retry mantığı yazılırken

---

## Rules

- HTTP 429 → `RateLimitError` (retryable).
- `Retry-After` header varsa o kadar bekle, yoksa exponential backoff.
- Backoff: `2^attempt * base_delay` saniye, max 60 saniye.
- 3 rate limit sonrası → bu provider'dan vazgeç, next'e geç.
- Jitter ekle: `backoff + random.uniform(0, 1)` — thundering herd önleme.

---

## Guidelines

Rate limit handling:
```python
import random
import asyncio

BASE_DELAY = 2  # saniye
MAX_DELAY = 60  # saniye
MAX_RETRIES = 3


async def call_with_rate_limit_retry(
    call_func: Callable,
    *args,
    **kwargs
) -> Any:
    for attempt in range(MAX_RETRIES):
        try:
            return await call_func(*args, **kwargs)
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After")
                
                if retry_after:
                    wait_time = float(retry_after)
                else:
                    wait_time = min(
                        BASE_DELAY * (2 ** attempt) + random.uniform(0, 1),
                        MAX_DELAY
                    )
                
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"{wait_time:.1f}s bekleniyor"
                )
                await asyncio.sleep(wait_time)
                continue
            
            raise  # 429 değilse direkt fırlat
    
    raise RateLimitError(f"Rate limit: {MAX_RETRIES} denemeden sonra başarısız")
```

Provider rotasyonu:
```python
# 3 rate limit sonrası provider değiştir
if isinstance(error, RateLimitError) and error.count >= 3:
    logger.warning("Rate limit eşiği aşıldı, sonraki provider'a geçiliyor")
    continue  # fallback zincirinde bir sonraki provider
```

---

## References

- `provider-fallback-chain-skill/SKILL.md` — fallback zinciri
- `retry-decorator-implementation-skill/SKILL.md` — retry decorator
- `exponential-backoff-calculation-skill/SKILL.md` — backoff hesaplama
