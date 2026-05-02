---
name: api-rate-limit-handling
description: Coder AI için — LLM veya harici API'lerin hız limitlerini (rate limit) yönetmek; 429 hatasında akıllı bekleme uygulamak.
---

## Purpose

Rate limit aşıldığında saf retry döngüsü hataları çarpar ve çabuk tüketir.
Akıllı yönetim: Retry-After başlığını okur, exponential backoff ile bekler.
Token bucket veya leaky bucket ile proaktif yavaşlama da sağlanır.

---

## When to Apply

- LLM API `429 Too Many Requests` döndürdüğünde
- Yüksek hacimli LLM çağrısında proaktif yavaşlama gerektiğinde
- OpenRouter veya Gemini rate limit bilgileri kullanılırken

---

## Rules

- 429 alınca: `Retry-After` başlığı okunur, o kadar beklenir.
- Başlık yoksa: exponential backoff (5s, 10s, 20s, 40s).
- Max bekleme: 120 saniye.
- Rate limit persistent olursa: fallback provider'a geç.

---

## Guidelines

```python
import asyncio
import time
from typing import Any

class RateLimitHandler:
    def __init__(self, max_retries: int = 4, base_delay: float = 5.0):
        self._max_retries = max_retries
        self._base_delay  = base_delay
        self._last_429_at: float = 0.0
    
    async def call_with_rate_limit(
        self,
        fn,
        *args,
        **kwargs,
    ) -> Any:
        for attempt in range(self._max_retries):
            try:
                return await fn(*args, **kwargs)
            except Exception as exc:
                if not self._is_rate_limit(exc):
                    raise
                
                delay = self._extract_retry_after(exc)
                if delay is None:
                    delay = min(self._base_delay * (2 ** attempt), 120.0)
                
                self._last_429_at = time.time()
                await asyncio.sleep(delay)
        
        raise RuntimeError(f"Rate limit aşıldı, {self._max_retries} denemeden sonra")
    
    def _is_rate_limit(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return "429" in msg or "rate limit" in msg or "too many" in msg
    
    def _extract_retry_after(self, exc: Exception) -> float | None:
        import re
        match = re.search(r"retry.after[:\s]+(\d+)", str(exc), re.I)
        return float(match.group(1)) if match else None
    
    @property
    def seconds_since_last_limit(self) -> float:
        return time.time() - self._last_429_at if self._last_429_at else float("inf")

# Kullanım
handler = RateLimitHandler()

async def safe_llm_call(llm, messages):
    return await handler.call_with_rate_limit(llm.ainvoke, messages)
```

---

## References

- `retry-decision-logic-skill/SKILL.md` — retry kararı
- `retry-with-jitter-skill/SKILL.md` — jitter ile retry
- `model-fallback-chain-skill/SKILL.md` — model fallback zinciri
