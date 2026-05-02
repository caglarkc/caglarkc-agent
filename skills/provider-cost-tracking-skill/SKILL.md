---
name: provider-cost-tracking
description: Coder AI için — LLM provider kullanım maliyetini token başına hesaplamak ve sprint toplam maliyetini raporlamak.
---

## Purpose

LLM çağrıları ücretsiz değil — her sprint ne kadar harcandı bilinmeli.
Maliyet takibi: hangi model, kaç token, tahmini USD.
Bütçe aşımında uyarı veya daha ucuz modele geçiş tetiklenir.

---

## When to Apply

- Her LLM çağrısı sonrası token sayımı güncellenirken
- Sprint sonu maliyet özeti hazırlanırken
- Token bütçesi kontrol edilirken

---

## Rules

- Fiyatlar: USD / 1M token cinsinden tanımlanır.
- Input ve output token ayrı izlenir.
- Güncel fiyatlar ortam değişkeni veya config'den okunur.
- Tahmini maliyet — gerçek faturalama değil.

---

## Guidelines

```python
from dataclasses import dataclass, field

# USD per 1M tokens (örnek, güncel değil)
PROVIDER_PRICING: dict[str, dict] = {
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gpt-4o-mini":      {"input": 0.15, "output": 0.60},
    "claude-haiku":     {"input": 0.25, "output": 1.25},
    "ollama":           {"input": 0.0,  "output": 0.0},
}

@dataclass
class UsageRecord:
    model: str
    input_tokens:  int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

@dataclass
class CostTracker:
    records: list[UsageRecord] = field(default_factory=list)
    
    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = PROVIDER_PRICING.get(model, {"input": 0.0, "output": 0.0})
        cost = (
            input_tokens  / 1_000_000 * pricing["input"] +
            output_tokens / 1_000_000 * pricing["output"]
        )
        self.records.append(UsageRecord(model, input_tokens, output_tokens, cost))
        return cost
    
    @property
    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.records)
    
    @property
    def total_tokens(self) -> int:
        return sum(r.input_tokens + r.output_tokens for r in self.records)
    
    def summary(self) -> str:
        return (
            f"Toplam maliyet: ${self.total_cost:.4f}\n"
            f"Toplam token : {self.total_tokens:,}\n"
            f"Çağrı sayısı : {len(self.records)}"
        )
```

---

## References

- `token-budget-management-skill/SKILL.md` — token bütçesi
- `sprint-resource-limits-skill/SKILL.md` — kaynak sınırları
- `llm-provider-selection-skill/SKILL.md` — provider seçimi
