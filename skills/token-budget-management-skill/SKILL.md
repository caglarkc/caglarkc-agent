---
name: token-budget-management
description: Planner AI için — her sprint için LLM token bütçesini takip etmek; aşırı tüketimi erkenden tespit edip optimize etmek.
---

## Purpose

Sınırsız token kullanımı API maliyetini patlatır.
Token bütçesi belirlenirse her sprint için harcama öngörülür.
Bütçe aşımı uyarısı provider değişikliği veya prompt optimizasyonu tetikler.

---

## When to Apply

- Sprint başlarken token bütçesi belirlenirken
- LLM çağrısı yapıldığında tüketim loglanırken
- Bütçe aşımı tespit edildiğinde uyarı üretilirken

---

## Rules

- Token bütçesi: sprint başında belirlenir (varsayılan 100K token).
- Her LLM çağrısı sonrası tüketim state'e eklenir.
- %80 kullanımda uyarı, %100'de fallback provider devreye girer.
- Bütçe: Gemini ve Ollama için ayrı sayaç.

---

## Guidelines

```python
from dataclasses import dataclass, field

@dataclass
class TokenBudget:
    total: int = 100_000
    used: int = 0
    warning_threshold: float = 0.8
    
    @property
    def remaining(self) -> int:
        return self.total - self.used
    
    @property
    def usage_pct(self) -> float:
        return self.used / self.total if self.total > 0 else 0.0
    
    @property
    def is_warning(self) -> bool:
        return self.usage_pct >= self.warning_threshold
    
    @property
    def is_exhausted(self) -> bool:
        return self.used >= self.total
    
    def consume(self, tokens: int) -> None:
        self.used += tokens

def update_token_budget(
    state: OrchestratorState,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    budget_dict = state.get("token_budget", {"total": 100_000, "used": 0})
    budget = TokenBudget(**budget_dict)
    budget.consume(input_tokens + output_tokens)
    
    if budget.is_warning and not budget.is_exhausted:
        logger.warning(
            f"Token bütçesi uyarısı: {budget.usage_pct:.0%} kullanıldı "
            f"({budget.used:,}/{budget.total:,})"
        )
    
    return {"token_budget": {"total": budget.total, "used": budget.used}}
```

---

## References

- `telemetry-logging-skill/SKILL.md` — token loglama
- `llm-provider-selection-skill/SKILL.md` — provider geçişi
- `sprint-metrics-collection-skill/SKILL.md` — metrikler
