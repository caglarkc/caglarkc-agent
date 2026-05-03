---
name: code-refactor-suggestion
description: Coder AI için — üretilen veya mevcut kodda refactor fırsatlarını tespit edip önermek.
---

## Purpose

Hızlı üretilen kod çalışır ama bakımı zordur.
Refactor önerileri: tekrar eden bloklar, uzun fonksiyonlar, kötü isimler.
Reviewer node bu önerileri oluşturur, uygulama planner kararına kalır.

---

## When to Apply

- Reviewer node kod kalitesi değerlendirirken
- Üretilen dosya 150 satırı geçtiğinde
- Aynı mantık birden fazla dosyada göründüğünde

---

## Rules

- Öneri: somut, uygulanabilir — "bu iyidir" değil.
- Öncelik: yüksek (hata riski), orta (bakım), düşük (stil).
- Uygulama: planner kararına bırakılır, zorunlu değil.
- Max 5 öneri per dosya (fazlası gürültü).

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class RefactorSuggestion:
    priority: str  # "high" | "medium" | "low"
    category: str  # "duplication" | "complexity" | "naming" | "structure"
    description: str
    location: str  # "line X" veya "function Y"

REFACTOR_PROMPT = """
Şu Python kodunu incele ve refactor önerisi sun.
Her öneri için: öncelik, kategori, açıklama ve konum belirt.
Max 5 öneri, JSON dizisi olarak döndür.

Kod:
{code}
"""

def parse_refactor_suggestions(llm_output: str) -> list[RefactorSuggestion]:
    import json, re
    json_match = re.search(r'\[.*\]', llm_output, re.DOTALL)
    if not json_match:
        return []
    try:
        items = json.loads(json_match.group())
        return [
            RefactorSuggestion(
                priority=item.get("priority", "low"),
                category=item.get("category", "structure"),
                description=item.get("description", ""),
                location=item.get("location", ""),
            )
            for item in items[:5]
        ]
    except (json.JSONDecodeError, KeyError):
        return []

def format_suggestions(suggestions: list[RefactorSuggestion]) -> str:
    if not suggestions:
        return "Refactor önerisi yok."
    lines = ["Refactor önerileri:"]
    for s in suggestions:
        lines.append(f"  [{s.priority.upper()}] {s.location}: {s.description}")
    return "\n".join(lines)
```

---

## References

- `code-review-checklist-skill/SKILL.md` — kod inceleme
- `reviewer-node-implementation-skill/SKILL.md` — reviewer node
- `technical-debt-logging-skill/SKILL.md` — teknik borç kaydı
