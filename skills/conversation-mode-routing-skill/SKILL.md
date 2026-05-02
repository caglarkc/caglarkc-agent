---
name: conversation-mode-routing
description: Planner AI için — gelen kullanıcı mesajını analiz ederek doğru PM moduna yönlendirmek; sohbet mu planlama mı onay mı olduğuna karar vermek.
---

## Purpose

Kullanıcı mesajı farklı niyetler taşıyabilir — yanlış mod seçilirse yanlış yanıt verilir.
"Dur" mesajı SOHBET gibi görünür ama SPRINT_CANCEL tetikler.
Routing mantığı, mesajdan niyeti doğru çıkarır.

---

## When to Apply

- Her yeni kullanıcı mesajı işlenirken
- PM node'un başında mod seçimi yapılırken
- Ambiguous mesajlar analiz edilirken

---

## Rules

- Açık komutlar (`/approve`, `/status`) doğrudan yönlendirilir.
- Doğal dil: LLM veya keyword ile intent tespit edilir.
- "Onaylıyorum", "evet", "tamam" → approval.
- "Dur", "iptal", "hayır" → rejection veya cancellation.
- Belirsiz mesaj: `[SOHBET]` modunda açıklama istenir.

---

## Guidelines

```python
from enum import Enum

class ConversationIntent(str, Enum):
    CHAT = "chat"
    PLAN = "plan"
    APPROVE = "approve"
    REJECT = "reject"
    STATUS = "status"
    CANCEL = "cancel"

APPROVAL_KEYWORDS = {"evet", "tamam", "onaylıyorum", "başlat", "devam"}
REJECTION_KEYWORDS = {"hayır", "dur", "reddet", "değiştir", "iptal"}
STATUS_KEYWORDS = {"durum", "ne oldu", "bitti mi", "ilerleme", "kaç"}
CANCEL_KEYWORDS = {"iptal", "bırak", "sonlandır", "kapat"}

def detect_intent(
    message: str,
    current_mode: str,
) -> ConversationIntent:
    msg_lower = message.lower().strip()
    
    # Explicit commands
    if msg_lower.startswith("/approve"):
        return ConversationIntent.APPROVE
    if msg_lower.startswith("/reject"):
        return ConversationIntent.REJECT
    if msg_lower.startswith("/status"):
        return ConversationIntent.STATUS
    
    # Keyword matching
    words = set(msg_lower.split())
    if words & APPROVAL_KEYWORDS and current_mode == "waiting_approval":
        return ConversationIntent.APPROVE
    if words & REJECTION_KEYWORDS and current_mode == "waiting_approval":
        return ConversationIntent.REJECT
    if words & STATUS_KEYWORDS:
        return ConversationIntent.STATUS
    if words & CANCEL_KEYWORDS:
        return ConversationIntent.CANCEL
    
    # Default: planning or chat
    if any(kw in msg_lower for kw in ["yap", "ekle", "oluştur", "yaz"]):
        return ConversationIntent.PLAN
    
    return ConversationIntent.CHAT
```

---

## References

- `pm-mode-skill/SKILL.md` — PM modları
- `mode-transition-detection-skill/SKILL.md` — mod geçişi
- `execution-intent-detection-skill/SKILL.md` — yürütme niyeti
