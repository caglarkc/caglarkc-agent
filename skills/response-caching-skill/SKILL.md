---
name: response-caching
description: Coder AI için — tekrarlayan LLM sorgularının yanıtlarını önbelleğe almak; aynı prompt için ikinci kez LLM çağrısı yapmamak.
---

## Purpose

Aynı soru (proje bağlamı, şablon üretimi) farklı sprint'lerde tekrar edilebilir.
Response cache ikinci çağrıyı token ve zaman tasarrufu ile yanıtlar.
Deterministik prompt + düşük temperature kombinasyonu caching'i güvenli yapar.

---

## When to Apply

- Aynı prompt birden fazla kez çağrılıyorsa
- Test ortamında gerçek LLM çağrısı yapılmak istemiyorsa
- Pahalı Gemini çağrıları optimize edilmek istendiğinde

---

## Rules

- Cache anahtarı: hash(prompt_string).
- TTL: 1 saat — eski yanıtlar geçersiz olabilir.
- Cache sadece deterministik (temperature≤0.2) çağrılar için.
- Production'da opsiyonel — geliştirme ortamında faydalı.

---

## Guidelines

```python
import hashlib
from datetime import datetime, timedelta

class LLMResponseCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[str, tuple[str, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, messages: list) -> str:
        content = str([(m.__class__.__name__, m.content) for m in messages])
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get(self, messages: list) -> str | None:
        key = self._make_key(messages)
        if key not in self._store:
            self._misses += 1
            return None
        
        response, expires = self._store[key]
        if datetime.utcnow() > expires:
            del self._store[key]
            self._misses += 1
            return None
        
        self._hits += 1
        logger.debug(f"Cache hit [{key}] (hits={self._hits})")
        return response
    
    def set(self, messages: list, response: str) -> None:
        key = self._make_key(messages)
        self._store[key] = (response, datetime.utcnow() + self._ttl)

# Cached LLM wrapper
class CachedLLM:
    def __init__(self, llm: BaseChatModel, cache: LLMResponseCache):
        self._llm = llm
        self._cache = cache
    
    async def ainvoke(self, messages: list) -> BaseMessage:
        cached = self._cache.get(messages)
        if cached is not None:
            return AIMessage(content=cached)
        
        response = await self._llm.ainvoke(messages)
        self._cache.set(messages, response.content)
        return response
```

---

## References

- `caching-patterns-skill/SKILL.md` — genel cache
- `llm-provider-selection-skill/SKILL.md` — provider
- `telemetry-logging-skill/SKILL.md` — cache hit/miss logu
