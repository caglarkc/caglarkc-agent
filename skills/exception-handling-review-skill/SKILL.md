---
name: exception-handling-review
description: Planner AI için — hata yakalama mantığının doğru exception tiplerini kullandığını, bare except olmadığını, hataların log'landığını ve uygun şekilde propagate edildiğini review sırasında kontrol etmek.
---

## Purpose

Yetersiz veya hatalı exception handling'i yakalar.
`except Exception: pass` gibi sessiz başarısızlıklar debug'ı imkânsız kılar.
Hataların kullanıcıya veya state'e doğru şekilde iletildiğini garantiler.

---

## When to Apply

- Her dış çağrı (LLM, DB, HTTP, dosya) review edilirken
- try/except bloğu içeren kod review edilirken
- Worker veya node hata handling'i kontrol edilirken

---

## Rules

- Bare `except:` veya `except Exception: pass` yasak.
- Her exception en az `logger.error()` ile log'lanmalı.
- Dış servis hatası (LLM, HTTP): spesifik exception tipi yakalanmalı.
- State'e hata kaydı: `errors` listesine structured dict eklenmeli.
- Retryable hata tespiti: `WorkerFailureLog.retryable` doğru set edilmeli.
- `finally` bloğu kaynak temizliği için kullanılmalı (connection, lock).
- Exception chaining: `raise NewError("msg") from original_error`.

---

## Guidelines

Doğru exception handling:
```python
# DOĞRU
async def call_llm(prompt: str) -> str:
    try:
        response = await llm_client.generate(prompt)
        return response.text
    except httpx.TimeoutException as e:
        logger.error(f"LLM timeout: {e}", extra={"prompt_length": len(prompt)})
        raise LLMTimeoutError("LLM yanıt vermedi") from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning("Rate limit hit, retrying...")
            raise RateLimitError("Rate limit") from e
        raise LLMError(f"HTTP {e.response.status_code}") from e

# YANLIŞ
async def call_llm(prompt: str) -> str:
    try:
        return await llm_client.generate(prompt)
    except:  # bare except — her şeyi yakalar, sessizce devam
        pass
```

State'e hata kaydı:
```python
# Node içinde hata kaydetme
except Exception as e:
    logger.exception(f"Planner hatası: {e}")
    return {
        "errors": state.get("errors", []) + [{
            "node": "planner",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
```

---

## References

- `custom-exception-hierarchy-skill/SKILL.md` — exception tipleri
- `structured-error-logging-skill/SKILL.md` — log formatı
- `retry-decorator-implementation-skill/SKILL.md` — retry mantığı
