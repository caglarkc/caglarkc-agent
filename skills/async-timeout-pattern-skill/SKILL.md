---
name: async-timeout-pattern
description: Coder AI için — asyncio.wait_for ile async operasyonlara zaman aşımı eklemek; takılı kalan işlemleri belirli süre sonra iptal etmek.
---

## Purpose

LLM çağrısı veya DB sorgusu sonsuza kadar bekleyebilir.
`asyncio.wait_for(coro, timeout=N)` belirli süre sonra `TimeoutError` fırlatır.
Takılı operasyonlar sistemi bloklamaz.

---

## When to Apply

- LLM `ainvoke` çağrısında timeout gerektiğinde
- DB sorgusu timeout ile korunurken
- Network çağrısı sınırlı süreyle yapılırken

---

## Rules

- Her dış servis çağrısına timeout eklenir.
- LLM: 60 saniye varsayılan.
- DB: 10 saniye.
- Network: 30 saniye.
- `TimeoutError`: retry kararına gönderilir.

---

## Guidelines

```python
import asyncio

TIMEOUT_LLM = 60.0
TIMEOUT_DB  = 10.0
TIMEOUT_NET = 30.0

async def llm_invoke_with_timeout(
    llm: BaseChatModel,
    messages: list,
    timeout: float = TIMEOUT_LLM,
) -> BaseMessage:
    try:
        return await asyncio.wait_for(
            llm.ainvoke(messages),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise TimeoutError(
            f"LLM yanıt vermedi ({timeout}s)"
        )

async def db_query_with_timeout(
    coro,
    timeout: float = TIMEOUT_DB,
):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"DB sorgusu zaman aşımına uğradı ({timeout}s)")

# Toplu timeout: birden fazla operasyon
async def gather_with_timeout(
    *coros,
    timeout: float = 120.0,
) -> list:
    try:
        return await asyncio.wait_for(
            asyncio.gather(*coros, return_exceptions=True),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"Paralel operasyonlar zaman aşımına uğradı ({timeout}s)")

# Graceful timeout: timeout olursa default döndür
async def with_default_on_timeout(coro, default, timeout: float):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Timeout — default değer kullanılıyor")
        return default
```

---

## References

- `retry-decision-logic-skill/SKILL.md` — timeout → retry karar
- `approval-timeout-handling-skill/SKILL.md` — onay timeout
- `async-function-template-skill/SKILL.md` — async şablon
