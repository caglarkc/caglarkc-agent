---
name: context-window-management
description: Coder AI için — LLM'e gönderilen prompt'un token limitini aşmaması için context içeriğini akıllıca kırpma ve önceliklendirme.
---

## Purpose

Token limitini aşan prompt LLM'in yanıt vermemesine veya hata vermesine yol açar.
Kritik bilgiyi koruyarak fazla içeriği kırpar.
Model başına farklı token limitlerini yönetir.

---

## When to Apply

- `src/core/llm_providers.py`'de prompt oluşturulurken
- `src/core/manager_planning.py`'de conversation history gönderilirken
- Related files context eklenirken

---

## Rules

- Context max: 4000 char (model limitinin güvenli tahmini).
- Related files max: 1800 char.
- Conversation history: son 20 tur saklanır, daha fazlası kırpılır.
- Kırpma sırası: en eski bilgiler önce kırpılır.
- Kritik bilgi (görev açıklaması, hedef dosya) hiçbir zaman kırpılmaz.

---

## Guidelines

Context kırpma:
```python
MAX_CONTEXT_CHARS = 4000
MAX_RELATED_FILES_CHARS = 1800
MAX_HISTORY_TURNS = 20


def truncate_context(context: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    if len(context) <= max_chars:
        return context
    # Son MAX_CONTEXT_CHARS karakteri al (en yeni bilgi öncelikli)
    return "...(kırpıldı)...\n" + context[-max_chars:]


def truncate_related_files(files_content: str) -> str:
    if len(files_content) <= MAX_RELATED_FILES_CHARS:
        return files_content
    return files_content[:MAX_RELATED_FILES_CHARS] + "\n...(kırpıldı)..."


def trim_conversation_history(history: list[dict]) -> list[dict]:
    """Son MAX_HISTORY_TURNS tur tut."""
    max_entries = MAX_HISTORY_TURNS * 2  # her tur: user + manager
    if len(history) <= max_entries:
        return history
    return history[-max_entries:]
```

Token tahmini (basit):
```python
def estimate_tokens(text: str) -> int:
    """Kaba tahmin: 1 token ≈ 4 karakter (İngilizce için)."""
    return len(text) // 4

MAX_TOKENS = 8000  # güvenli limit

def build_safe_prompt(system: str, context: str, task: str) -> tuple[str, str, str]:
    available = MAX_TOKENS - estimate_tokens(system) - estimate_tokens(task) - 100
    
    if estimate_tokens(context) > available:
        # Fazladan karakterleri kırp
        max_chars = available * 4
        context = "...\n" + context[-max_chars:]
    
    return system, context, task
```

---

## References

- `prompt-construction-pattern-skill/SKILL.md` — prompt yapısı
- `chat-model-invocation-skill/SKILL.md` — model çağrısı
- `multi-turn-context-preservation-skill/SKILL.md` — geçmiş yönetimi
