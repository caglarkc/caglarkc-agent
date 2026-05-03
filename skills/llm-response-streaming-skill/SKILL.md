---
name: llm-response-streaming
description: Coder AI için — LLM yanıtını astream() ile token token okumak; uzun çıktıları kullanıcıya anlık göstermek.
---

## Purpose

Uzun kod üretimi sırasında kullanıcı boş ekrana bakar.
Streaming: her token gelince gösterilir — progress hissi yaratır.
Büyük dosya üretimi için de bellek verimlidir.

---

## When to Apply

- Kullanıcıya görünür ilerleme gösterilmek istediğinde
- 200+ satır kod üretiminde
- CLI veya WebSocket üzerinden canlı çıktı aktarılırken

---

## Rules

- Streaming: `llm.astream()` kullanılır.
- Buffer: her 10 token'da bir ekrana flush et.
- Timeout: streaming başlarsa 5 dakika, başlamazsa 30s.
- Hata: streaming yarıda kesilirse toplanan kısım döndürülür.

---

## Guidelines

```python
import asyncio
from typing import AsyncIterator

async def stream_llm_response(
    llm,
    messages: list,
    on_token=None,  # Callable[[str], None] | None
) -> str:
    buffer = []
    
    try:
        async for chunk in llm.astream(messages):
            token = chunk.content if hasattr(chunk, "content") else str(chunk)
            buffer.append(token)
            if on_token:
                on_token(token)
        return "".join(buffer)
    except Exception as exc:
        if buffer:
            # Kısmi çıktı döndür
            return "".join(buffer)
        raise

async def stream_to_stdout(llm, messages: list) -> str:
    import sys
    
    def print_token(token: str) -> None:
        sys.stdout.write(token)
        sys.stdout.flush()
    
    result = await stream_llm_response(llm, messages, on_token=print_token)
    print()  # Yeni satır
    return result

async def stream_with_timeout(
    llm,
    messages: list,
    timeout: float = 300.0,
) -> str:
    try:
        return await asyncio.wait_for(
            stream_llm_response(llm, messages),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"Streaming {timeout}s içinde tamamlanmadı")

# WebSocket üzerinden streaming
async def stream_to_websocket(
    llm,
    messages: list,
    websocket,
) -> str:
    buffer = []
    
    async def send_token(token: str) -> None:
        buffer.append(token)
        await websocket.send_text(token)
    
    return await stream_llm_response(llm, messages, on_token=None)
```

---

## References

- `streaming-response-handling-skill/SKILL.md` — streaming yanıt
- `async-timeout-pattern-skill/SKILL.md` — async timeout
- `async-generator-pattern-skill/SKILL.md` — async generator
