---
name: exponential-backoff-calculation
description: Coder AI için — retry beklemelerini 2^n * base_delay formülüyle hesaplama, jitter ekleme ve maksimum gecikme sınırlama.
---

## Purpose

Retry beklemelerini tutarlı ve güvenli hesaplar.
Jitter olmadan tüm retry'lar aynı anda tetiklenir (thundering herd).
Max delay ile sınırlama yapmak sunucu aşırı yüklenmesini önler.

---

## When to Apply

- Retry decorator beklemesi hesaplanırken
- Rate limit sonrası bekleme süresi belirlenirken
- Worker başarısız sonrası yeniden atama zamanı planlanırken

---

## Rules

- Formül: `delay = min(base_delay * (2 ** attempt) + jitter, max_delay)`.
- `base_delay`: 2 saniye (LLM provider için).
- `max_delay`: 60 saniye.
- Jitter: `random.uniform(0, 1)` — küçük rastgele sapma.
- Attempt 0'dan başlar (ilk deneme başarısız → attempt=0 → 2s bekleme).

---

## Guidelines

Backoff hesaplama:
```python
import random
import asyncio


def calculate_backoff(
    attempt: int,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    attempt=0 → 2s (+ jitter)
    attempt=1 → 4s (+ jitter)  
    attempt=2 → 8s (+ jitter)
    attempt=3 → 16s (+ jitter)
    attempt=4+ → 60s (max_delay)
    """
    delay = base_delay * (2 ** attempt)
    if jitter:
        delay += random.uniform(0, 1)
    return min(delay, max_delay)


# Kullanım örneği
async def retry_with_backoff(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await func()
        except RetryableError as e:
            if attempt < max_attempts - 1:
                wait = calculate_backoff(attempt)
                logger.warning(f"Retry {attempt+1}/{max_attempts}, {wait:.1f}s bekleniyor")
                await asyncio.sleep(wait)
    raise  # son denemede de başarısızsa

# Bu proje için standart değerler:
# LLM provider: base=2, max=60
# DB retry: base=0.5, max=10
# HTTP retry: base=1, max=30
```

Bekleme tablosu:
```
Attempt 0: 2.0s + jitter
Attempt 1: 4.0s + jitter
Attempt 2: 8.0s + jitter
Attempt 3: 16.0s + jitter
Attempt 4: 32.0s + jitter
Attempt 5+: 60.0s (max)
```

---

## References

- `retry-decorator-implementation-skill/SKILL.md` — retry decorator
- `rate-limit-handling-skill/SKILL.md` — rate limit
- `worker-failure-triage-skill/SKILL.md` — failure handling
