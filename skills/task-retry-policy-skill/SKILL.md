---
name: task-retry-policy
description: Planner AI için — her görev için ayrı retry politikası tanımlamak; hangi hatalar yeniden denenecek, kaç kez, ne kadar bekleyerek.
---

## Purpose

Tüm hataları aynı şekilde yeniden denemek israf veya döngüye neden olur.
Syntax hatası retry'dan yararlanmaz; network hatası yarar.
Görev bazlı politika, retry kararlarını akıllı hâle getirir.

---

## When to Apply

- Task tanımı oluşturulurken retry limitleri belirlenirken
- Hata kategorisine göre retry kararı verilirken
- Retry sayacı güncellenmeden önce politika kontrol edilirken

---

## Rules

- Her task'ın `retry_policy` alanı olur.
- Varsayılan: maks 3 deneme, 5s bekleme, exponential backoff.
- Retryable hatalar: timeout, network, LLM rate limit.
- Non-retryable: syntax error, auth failure, missing dependency.
- Maks deneme aşılırsa: task `failed_permanently` olarak işaretlenir.

---

## Guidelines

```python
from dataclasses import dataclass, field
from enum import Enum

class RetryStrategy(str, Enum):
    FIXED       = "fixed"
    EXPONENTIAL = "exponential"
    NONE        = "none"

@dataclass
class RetryPolicy:
    max_attempts: int     = 3
    base_delay:   float   = 5.0
    strategy:     RetryStrategy = RetryStrategy.EXPONENTIAL
    retryable_errors: list[str] = field(default_factory=lambda: [
        "TimeoutError", "ConnectionError", "RateLimitError",
    ])

DEFAULT_POLICIES = {
    "llm_generation": RetryPolicy(max_attempts=3, base_delay=10.0),
    "db_write":       RetryPolicy(max_attempts=5, base_delay=2.0),
    "validation":     RetryPolicy(max_attempts=2, base_delay=1.0),
    "network":        RetryPolicy(max_attempts=4, base_delay=5.0),
}

def get_retry_delay(policy: RetryPolicy, attempt: int) -> float:
    if policy.strategy == RetryStrategy.EXPONENTIAL:
        return policy.base_delay * (2 ** (attempt - 1))
    return policy.base_delay

def should_retry(
    error: Exception,
    attempt: int,
    policy: RetryPolicy,
) -> bool:
    if attempt >= policy.max_attempts:
        return False
    error_type = type(error).__name__
    return any(
        err in error_type or err in str(error)
        for err in policy.retryable_errors
    )

def apply_task_retry_policy(
    task: dict,
    error: Exception,
    attempt: int,
) -> dict:
    task_type = task.get("type", "llm_generation")
    policy = DEFAULT_POLICIES.get(task_type, RetryPolicy())
    
    if should_retry(error, attempt, policy):
        delay = get_retry_delay(policy, attempt)
        return {"action": "retry", "delay": delay, "attempt": attempt + 1}
    return {"action": "fail", "reason": str(error)}
```

---

## References

- `retry-decision-logic-skill/SKILL.md` — retry karar mantığı
- `retry-with-jitter-skill/SKILL.md` — jitter ile retry
- `error-categorization-skill/SKILL.md` — hata kategorileme
