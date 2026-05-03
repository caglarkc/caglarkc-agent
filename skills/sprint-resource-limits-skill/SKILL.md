---
name: sprint-resource-limits
description: Planner AI için — sprint boyunca kaynak kullanımını (token, süre, dosya sayısı) sınırlamak ve aşım durumunda uyarmak.
---

## Purpose

Sınırsız sprint yüksek maliyet veya askıda kalan işlem demektir.
Kaynak limitleri, sprint'in öngörülebilir bitiş koşullarını tanımlar.
Aşım: kullanıcı uyarılır veya sprint otomatik durdurulur.

---

## When to Apply

- Sprint başlarken bütçe/limit belirlenmesi istendiğinde
- Token sayacı eşiğe yaklaştığında uyarı verilirken
- Uzun süren sprint otomatik durdurulurken

---

## Rules

- Limitler: max_tokens, max_minutes, max_files, max_retries.
- Her LLM çağrısı sonrası token sayacı güncellenir.
- %80 eşiğinde uyarı, %100'de dur.
- Limit aşımı: state'e kaydedilir, kullanıcıya bildirilir.

---

## Guidelines

```python
from dataclasses import dataclass, field

@dataclass
class SprintResourceLimits:
    max_tokens:  int   = 500_000
    max_minutes: float = 60.0
    max_files:   int   = 50
    max_retries: int   = 30

@dataclass
class SprintResourceUsage:
    tokens_used:  int   = 0
    elapsed_minutes: float = 0.0
    files_processed: int  = 0
    retry_count:  int   = 0

def check_limits(
    usage: SprintResourceUsage,
    limits: SprintResourceLimits,
) -> dict:
    warnings = []
    hard_stop = False
    
    checks = [
        ("tokens",  usage.tokens_used,       limits.max_tokens),
        ("minutes", usage.elapsed_minutes,   limits.max_minutes),
        ("files",   usage.files_processed,   limits.max_files),
        ("retries", usage.retry_count,        limits.max_retries),
    ]
    
    for name, used, limit in checks:
        ratio = used / limit if limit else 0
        if ratio >= 1.0:
            hard_stop = True
            warnings.append(f"{name} limiti aşıldı ({used}/{limit})")
        elif ratio >= 0.8:
            warnings.append(f"{name} %{ratio*100:.0f} kullanıldı ({used}/{limit})")
    
    return {"warnings": warnings, "hard_stop": hard_stop}

def update_token_usage(state: dict, new_tokens: int) -> dict:
    current = state.get("tokens_used", 0)
    return {"tokens_used": current + new_tokens}
```

---

## References

- `token-budget-management-skill/SKILL.md` — token bütçe yönetimi
- `sprint-budget-estimation-skill/SKILL.md` — sprint bütçe tahmini
- `sprint-cancellation-skill/SKILL.md` — sprint iptal
