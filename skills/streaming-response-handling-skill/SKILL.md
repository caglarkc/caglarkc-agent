---
name: streaming-response-handling
description: Coder AI için — LLM streaming yanıtını (astream) işlemek; token token gelen yanıtı birleştirmek ve gerçek zamanlı çıktı göstermek.
---

## Purpose

Büyük kod dosyaları LLM'den tek yanıt olarak gelmesi uzun sürer.
Streaming, token gelirken gösterilmesini sağlar — kullanıcı bekler gibi hissetmez.
Kısmi çıktı alındığında işleme başlanabilir.

---

## When to Apply

- Worker veya planner LLM çağrısında gerçek zamanlı çıktı gerektiğinde
- Telegram'a canlı güncelleme gönderilirken
- CLI'da streaming çıktı gösterilirken

---

## Rules

- `astream()`: streaming için; `ainvoke()`: tek yanıt için.
- Streaming: chunk'lar birleştirilir → tam yanıt.
- Telegram: her N token'da mesaj güncellenir (edit_message).
- Streaming sırasında exception: biriktirilen yanıt loglanır.

---

## Guidelines

```python
async def stream_and_collect(
    llm: BaseChatModel,
    messages: list,
) -> str:
    """Streaming LLM yanıtını birleştirir."""
    chunks = []
    
    async for chunk in llm.astream(messages):
        if chunk.content:
            chunks.append(chunk.content)
    
    return "".join(chunks)

# CLI'da gerçek zamanlı çıktı
async def stream_to_console(
    llm: BaseChatModel,
    messages: list,
) -> str:
    full = []
    print("", end="", flush=True)
    
    async for chunk in llm.astream(messages):
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full.append(chunk.content)
    
    print()  # satır sonu
    return "".join(full)

# Telegram'a streaming (her 50 token güncelle)
async def stream_to_telegram(
    llm: BaseChatModel,
    messages: list,
    bot,
    chat_id: str,
    message_id: int,
    update_every: int = 50,
) -> str:
    accumulated = []
    token_count = 0
    
    async for chunk in llm.astream(messages):
        if not chunk.content:
            continue
        accumulated.append(chunk.content)
        token_count += 1
        
        if token_count % update_every == 0:
            current_text = "".join(accumulated)
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=current_text[-4000:],  # Telegram limiti
            )
    
    return "".join(accumulated)
```

---

## References

- `chat-model-invocation-skill/SKILL.md` — model çağrısı
- `telegram-command-handler-skill/SKILL.md` — Telegram
- `worker-node-implementation-skill/SKILL.md` — worker
