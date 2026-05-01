---
name: prompt-construction-pattern
description: Coder AI için — LLM provider'a gönderilecek system + user + context prompt'unu bu projeye özgü standart biçimde oluşturma.
---

## Purpose

LLM'e gönderilen prompt'un kalitesini ve tutarlılığını standartlaştırır.
Proje context, dosya bağlamı ve görev açıklamasının doğru birleştirilmesini sağlar.
Token limitini aşmadan maksimum context sağlar.

---

## When to Apply

- `src/core/llm_providers.py`'de worker prompt'u oluşturulurken
- `src/core/manager_planning.py`'de planner prompt'u oluşturulurken
- Yeni LLM çağrısı için prompt şablonu yazılırken

---

## Rules

- System prompt: proje mimarisi, kurallar, dil tercihleri.
- Context: ilgili dosyaların içeriği (max 4000 char).
- User message: görev açıklaması + hedef dosya bilgisi.
- Toplam token tahmini: system + context + user < model limiti.
- Hassas veri (API key) prompt'a dahil edilmez.
- Türkçe yorumlar için system prompt'ta belirtilir.

---

## Guidelines

Worker prompt şablonu:
```python
WORKER_SYSTEM_PROMPT = """Sen bir Python senior developer'sın.
Bu proje: AI Development Team Orchestrator (LangGraph tabanlı otonom geliştirme sistemi).

KURALLAR:
- Tüm I/O operasyonları async/await ile yazılır
- Type hint zorunlu (parametre + dönüş tipi)
- Dış çağrılar try/except ile sarılır
- Kod içi yorumlar Türkçe
- Commit yapma, sadece dosya içeriği üret
- pyproject.toml'daki paketler kullanılır

MİMARİ:
- src/graph/: LangGraph node'ları ve state
- src/core/: EventBus, StateManager, servisler
- src/storage/: SQLite repository
- src/interfaces/: CLI ve Telegram
- src/config/: Settings (Pydantic)
"""

def build_worker_prompt(
    task: dict,
    context: str,
    related_files: str
) -> list[BaseMessage]:
    return [
        SystemMessage(content=WORKER_SYSTEM_PROMPT),
        HumanMessage(content=f"""GÖREV: {task['description']}

HEDEF DOSYA: {task['target_file']}

PROJE CONTEXT:
{context[:4000]}

İLGİLİ DOSYALAR:
{related_files[:1800]}

Sadece {task['target_file']} dosyasının içeriğini üret.
Başka dosya veya açıklama ekleme.""")
    ]
```

Context oluşturma:
```python
def build_context(
    file_registry: dict,
    project_name: str,
    sprint_type: str
) -> str:
    lines = [
        f"Proje: {project_name}",
        f"Sprint tipi: {sprint_type}",
        f"Dosyalar: {', '.join(file_registry.keys())}"
    ]
    return "\n".join(lines)
```

---

## References

- `chat-model-invocation-skill/SKILL.md` — model çağrısı
- `context-window-management-skill/SKILL.md` — token limiti
- `provider-fallback-chain-skill/SKILL.md` — provider zinciri
