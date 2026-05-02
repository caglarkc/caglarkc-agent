---
name: retry-with-jitter
description: Coder AI için — exponential backoff'a rastgele jitter (gürültü) ekleyerek thundering herd sorununu önlemek; birden fazla worker'ın aynı anda retry yapmasını engellemek.
---

## Purpose

5 worker aynı anda fail olursa hepsi aynı anda retry yapar — provider yine çöker.
Jitter, her worker'ın farklı zamanda retry yapmasını sağlar.
Yük, zaman içine dağıtılır.

---

## When to Apply

- Çok sayıda worker aynı provider'a istek gönderirken
- Rate limit sorunları yaşandığında
- `retry_decorator_implementation` bekleme süresi hesaplanırken

---

## Rules

- Full jitter: `random.uniform(0, cap)` — önerilen.
- Equal jitter: `cap/2 + random.uniform(0, cap/2)`.
- Decorrelated jitter: `min(cap, random.uniform(base, prev*3))`.
- `cap`: maksimum bekleme süresi (örn. 60 saniye).

---

## Guidelines

```python
import random
import asyncio

def exponential_backoff_with_jitter(
    attempt: int,
    base: float = 1.0,
    cap: float = 60.0,
    multiplier: float = 2.0,
    strategy: str = "full",
) -> float:
    """
    Returns bekleme süresi (saniye).
    strategy: "full" | "equal" | "decorrelated"
    """
    exp = base * (multiplier ** attempt)
    
    if strategy == "full":
        return random.uniform(0, min(cap, exp))
    
    elif strategy == "equal":
        half = min(cap, exp) / 2
        return half + random.uniform(0, half)
    
    elif strategy == "decorrelated":
        # Decorrelated jitter — daha dağıtık
        prev = base * (multiplier ** max(0, attempt - 1))
        return min(cap, random.uniform(base, prev * 3))
    
    return min(cap, exp)

async def retry_with_jitter(
    coro_factory,
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> object:
    for attempt in range(max_attempts):
        try:
            return await coro_factory()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            delay = exponential_backoff_with_jitter(
                attempt, base=base_delay
            )
            logger.warning(
                f"Retry {attempt+1}/{max_attempts}: "
                f"{e}, {delay:.1f}s bekleniyor"
            )
            await asyncio.sleep(delay)
```

---

## References

- `exponential-backoff-calculation-skill/SKILL.md` — backoff
- `retry-decorator-implementation-skill/SKILL.md` — decorator
- `worker-concurrency-control-skill/SKILL.md` — eşzamanlılık
