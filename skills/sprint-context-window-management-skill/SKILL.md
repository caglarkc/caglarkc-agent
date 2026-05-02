---
name: sprint-context-window-management
description: Planner AI için — uzun sprint boyunca LLM bağlam penceresini yönetmek; önemli bilgiyi sıkıştırarak taşımak.
---

## Purpose

Sprint ilerledikçe mesaj geçmişi LLM context limitine yaklaşır.
Bağlam yönetimi: eski konuşmayı özete indirger, kritik bilgiyi korur.
Model yanıt kalitesi korunurken token israfı önlenir.

---

## When to Apply

- Konuşma geçmişi 50+ mesaj olduğunda
- Token sayacı context limitinin %70'ini aştığında
- Uzun sprint'te planner node'u çağrılmadan önce

---

## Rules

- Context penceresi: son 20 mesaj + sıkıştırılmış özet.
- Sıkıştırma: LLM ile özetleme (en fazla 500 token).
- Korunan bilgi: sprint hedefi, tamamlanan görevler, aktif görev.
- Sıkıştırma başarısız: ham mesajları kır (son 10 mesaj tut).

---

## Guidelines

```python
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

MAX_MESSAGES_BEFORE_COMPRESS = 50
KEEP_LAST_N = 20

async def compress_conversation(
    messages: list[BaseMessage],
    llm,
    sprint_context: dict,
) -> list[BaseMessage]:
    if len(messages) <= MAX_MESSAGES_BEFORE_COMPRESS:
        return messages
    
    to_compress = messages[:-KEEP_LAST_N]
    recent      = messages[-KEEP_LAST_N:]
    
    summary_prompt = (
        "Şu konuşmayı 3-5 cümleyle özetle. "
        "Sprint hedefi, tamamlanan görevler ve önemli kararları koru:\n\n"
        + "\n".join(f"{m.type}: {m.content[:200]}" for m in to_compress)
    )
    
    try:
        response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
        summary_msg = SystemMessage(
            content=f"[Geçmiş Özeti] {response.content}"
        )
        return [summary_msg] + recent
    except Exception:
        return recent  # Sıkıştırma başarısız, son N mesajı tut

def trim_messages_by_tokens(
    messages: list[BaseMessage],
    max_tokens: int = 8000,
    avg_chars_per_token: float = 4.0,
) -> list[BaseMessage]:
    result = []
    total_chars = 0
    
    for msg in reversed(messages):
        chars = len(msg.content)
        if total_chars + chars > max_tokens * avg_chars_per_token:
            break
        result.insert(0, msg)
        total_chars += chars
    
    return result
```

---

## References

- `conversation-history-trimming-skill/SKILL.md` — konuşma geçmişi kırpma
- `token-budget-management-skill/SKILL.md` — token bütçe yönetimi
- `context-injection-strategy-skill/SKILL.md` — bağlam enjeksiyonu
