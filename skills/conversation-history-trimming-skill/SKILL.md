---
name: conversation-history-trimming
description: Planner AI için — konuşma geçmişi büyüdüğünde context window'u taşmadan önce eski mesajları budamak; önemli bağlamı korumak.
---

## Purpose

LLM context window sınırlıdır — sonsuz konuşma geçmişi modeli yavaşlatır veya keser.
Önemli kararlar (plan onayları, ADR'ler) silinmez; sadece sıradan sohbet kısaltılır.
Token sayısı kontrol altında tutulur.

---

## When to Apply

- Konuşma geçmişi 50+ mesaja ulaştığında
- Token sayacı eşiği aştığında
- Yeni sprint başlarken önceki konuşmalar arşivlenirken

---

## Rules

- System mesajı asla silinmez.
- Son 10 kullanıcı/asistan mesajı her zaman korunur.
- Onay kararları içeren mesajlar (`[ONAY]`, `[KARAR]`) korunur.
- Sprint planı içeren mesajlar korunur.
- Kırpılan mesajlar sayısı log'a yazılır.

---

## Guidelines

```python
from typing import Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

MAX_MESSAGES = 40
KEEP_RECENT = 10

IMPORTANT_KEYWORDS = [
    "[ONAY]", "[KARAR]", "[PLANLAMA]", "[ADR-",
    "sprint", "onaylandı", "reddedildi"
]

def is_important(msg: BaseMessage) -> bool:
    content = str(msg.content)
    return any(kw in content for kw in IMPORTANT_KEYWORDS)

def trim_conversation_history(
    messages: Sequence[BaseMessage],
    max_messages: int = MAX_MESSAGES
) -> list[BaseMessage]:
    if len(messages) <= max_messages:
        return list(messages)
    
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    non_system = [m for m in messages if not isinstance(m, SystemMessage)]
    
    recent = non_system[-KEEP_RECENT:]
    older = non_system[:-KEEP_RECENT]
    
    # Önemli eski mesajları koru
    important_older = [m for m in older if is_important(m)]
    
    trimmed_count = len(older) - len(important_older)
    if trimmed_count > 0:
        logger.info(f"Konuşma geçmişi kırpıldı: {trimmed_count} mesaj silindi")
    
    return system_msgs + important_older + recent
```

State güncellemesi:
```python
# LangGraph state içinde
state["messages"] = trim_conversation_history(state["messages"])
```

---

## References

- `pm-mode-skill/SKILL.md` — PM konuşma yönetimi
- `graph-state-inspection-skill/SKILL.md` — state okuma
- `sprint-lifecycle-state-machine-skill/SKILL.md` — sprint sıfırlama
