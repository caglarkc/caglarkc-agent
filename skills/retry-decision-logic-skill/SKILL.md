---
name: retry-decision-logic
description: Coder AI için — bir görev başarısız olduğunda yeniden deneme yapılıp yapılmayacağına ve nasıl yapılacağına karar veren mantığı implemente etmek.
---

## Purpose

Her hata retry edilmez — bazıları kalıcı (4xx), bazıları geçici (5xx, timeout).
Yanlış retry hem zaman kaybettirir hem de rate limit'e çarpar.
Doğru retry kararı: hata tipi + deneme sayısı + backoff kombinasyonu.

---

## When to Apply

- Worker node'da hata yakalandığında
- Provider fallback öncesinde geçici hata mı kalıcı hata mı tespiti yapılırken
- `failed` durumuna geçiş koşulları yazılırken

---

## Rules

- `max_retries = 3` aşılırsa `failed` durumuna geç — daha fazla retry yok.
- HTTP 4xx: retry edilmez (client hatası).
- HTTP 5xx / timeout / connection error: retry edilir.
- `AuthenticationError`: retry edilmez — kalıcı hata.
- Her retry'dan önce exponential backoff uygulanır.

---

## Guidelines

Retry karar matrisi:
```python
from enum import Enum

class RetryDecision(Enum):
    RETRY = "retry"
    SKIP = "skip"       # bu dosyayı atla
    FAIL_PERMANENT = "fail_permanent"  # retry yok

PERMANENT_ERRORS = (
    AuthenticationError,
    PermissionError,
    ValueError,  # bad input
)

TRANSIENT_ERRORS = (
    TimeoutError,
    ConnectionError,
    asyncio.TimeoutError,
)

def decide_retry(
    error: Exception,
    attempt: int,
    max_retries: int = 3
) -> RetryDecision:
    if attempt >= max_retries:
        return RetryDecision.FAIL_PERMANENT
    
    if isinstance(error, PERMANENT_ERRORS):
        return RetryDecision.FAIL_PERMANENT
    
    # HTTP status code kontrolü
    status_code = getattr(error, "status_code", None)
    if status_code and 400 <= status_code < 500:
        return RetryDecision.FAIL_PERMANENT
    
    if isinstance(error, TRANSIENT_ERRORS):
        return RetryDecision.RETRY
    
    if status_code and status_code >= 500:
        return RetryDecision.RETRY
    
    # Belirsiz hatalar: retry
    return RetryDecision.RETRY
```

Worker'da kullanım:
```python
async def execute_with_retry(task: Task) -> TaskResult:
    attempt = 0
    while True:
        try:
            return await execute_task(task)
        except Exception as e:
            decision = decide_retry(e, attempt)
            if decision == RetryDecision.FAIL_PERMANENT:
                raise
            await asyncio.sleep(2 ** attempt)
            attempt += 1
```

---

## References

- `retry-decorator-implementation-skill/SKILL.md` — decorator pattern
- `provider-fallback-chain-skill/SKILL.md` — provider geçişi
- `cascading-failure-prevention-skill/SKILL.md` — hata yayılması
