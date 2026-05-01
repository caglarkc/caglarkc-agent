---
name: worker-failure-triage
description: Planner AI için — worker başarısızlığını analiz etmek; retryable mı, kalıcı mı, hangi worker'a atanacak, ne yapılacak kararını vermek.
---

## Purpose

Worker başarısızlığında doğru aksiyonu hızla belirler.
Retryable hata tekrar denenmeli; kalıcı hata farklı yaklaşım gerektirir.
Başarısız worker'ın yükü diğer worker'lara dengeli dağıtılır.

---

## When to Apply

- `worker.failed` event'i alındığında
- `WorkerFailureLog` kaydı oluştuğunda
- Dispatcher worker atama yaparken başarısızlık geçmişine baktığında
- Review node başarısız sprint değerlendirirken

---

## Rules

- Retryable hatalar: timeout, rate limit, geçici API hatası → retry.
- Kalıcı hatalar: invalid task description, dosya yazma izni, provider tamamen çöktü → revize.
- Başarısız worker aynı göreve maksimum 3 kez atanır.
- 3 denemeden sonra farklı provider veya farklı worker denenebilir.
- Tüm retry'lar tükendi → planner'a bildir, yeniden planlama.

---

## Guidelines

Hata sınıflandırma:
```python
RETRYABLE_ERRORS = [
    "TimeoutError",
    "RateLimitError",
    "ConnectionError",
    "HTTPStatusError 5xx",
    "JSONDecodeError",  # geçici parse hatası
]

PERMANENT_ERRORS = [
    "InvalidTaskError",
    "FilePermissionError",
    "ModelNotFoundError",
    "InvalidStateError",
]
```

Triage akışı:
```
worker.failed event:
1. last_error tipini kontrol et
2. attempt_count'u kontrol et
3. Karar:
   attempt < 3 AND retryable → retry (aynı görev, aynı veya farklı worker)
   attempt < 3 AND permanent → task revize et, planner'a ilet
   attempt >= 3 → escalate: sprint failed, kullanıcıya bildir
```

WorkerFailureLog kaydı:
```python
{
    "worker_id": "worker_a",
    "task_type": "write_file",
    "error_message": "TimeoutError: LLM 30s içinde yanıt vermedi",
    "retryable": True,
    "retry_count": 2,
    "recommendation": "Farklı provider dene (OpenRouter yerine Ollama)"
}
```

---

## References

- `retry-decision-logic-skill/SKILL.md` — retry kararı
- `cascading-failure-prevention-skill/SKILL.md` — zincirleme hata
- `worker-load-balancing-strategy-skill/SKILL.md` — yük dağılımı
