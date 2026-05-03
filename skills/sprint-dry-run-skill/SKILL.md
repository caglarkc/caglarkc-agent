---
name: sprint-dry-run
description: Planner AI için — sprint planını gerçek kod yazmadan simüle etmek; tahmini süre, kaynak kullanımı ve olası sorunları önceden görmek.
---

## Purpose

Beklenmedik sorunları gerçek sprint sırasında değil önce bulmak ister.
Dry run: planı çalıştırır ama hiçbir dosya yazmaz, LLM'e gerçek istek göndermez.
Simülasyon raporu: ne kadar sürer, kaç token, potansiyel riskler.

---

## When to Apply

- Büyük sprint başlatılmadan önce ön kontrol yapılırken
- Kullanıcı "ne kadar sürer?" sorusunu yanıtlamak için
- CI ortamında plan doğrulama aşamasında

---

## Rules

- Dry run: gerçek LLM çağrısı yok, stub sonuçlar.
- Süre tahmini: görev başına ortalama süre × görev sayısı.
- Token tahmini: prompt boyutu × görev sayısı.
- Çıktı: simülasyon raporu, gerçek state değişikliği yok.

---

## Guidelines

```python
from dataclasses import dataclass

STUB_LLM_RESPONSE_TOKENS = 500
AVG_PROMPT_TOKENS = 300

@dataclass
class DryRunReport:
    task_count:     int
    estimated_minutes: float
    estimated_tokens:  int
    estimated_cost_usd: float
    potential_risks: list[str]

def dry_run_sprint(
    tasks: list[dict],
    pricing_per_1m: float = 0.15,
) -> DryRunReport:
    task_count = len(tasks)
    total_min  = sum(t.get("estimated_minutes", 20) for t in tasks)
    total_tok  = task_count * (AVG_PROMPT_TOKENS + STUB_LLM_RESPONSE_TOKENS)
    cost       = total_tok / 1_000_000 * pricing_per_1m
    
    risks = []
    if task_count > 20:
        risks.append(f"Çok sayıda görev ({task_count}) — kapsam kayması riski")
    if total_min > 120:
        risks.append(f"Uzun sprint tahmini ({total_min} dk) — zaman aşımı riski")
    
    # Döngüsel bağımlılık kontrolü
    from collections import defaultdict
    deps = defaultdict(list)
    for t in tasks:
        for d in t.get("depends_on", []):
            deps[d].append(t["id"])
    
    # Basit döngü tespiti
    for task in tasks:
        for dep in task.get("depends_on", []):
            if task["id"] in deps.get(dep, []):
                risks.append(f"Döngüsel bağımlılık: {task['id']} ↔ {dep}")
    
    return DryRunReport(task_count, total_min, total_tok, cost, risks)

def format_dry_run_report(r: DryRunReport) -> str:
    lines = [
        "Dry Run Simülasyonu:",
        f"  Görev sayısı : {r.task_count}",
        f"  Tahmini süre : {r.estimated_minutes} dakika",
        f"  Token tahmini: {r.estimated_tokens:,}",
        f"  Maliyet tah. : ${r.estimated_cost_usd:.4f}",
    ]
    if r.potential_risks:
        lines.append("\n  Potansiyel Riskler:")
        for risk in r.potential_risks:
            lines.append(f"    ⚠ {risk}")
    return "\n".join(lines)
```

---

## References

- `sprint-what-if-analysis-skill/SKILL.md` — what-if analizi
- `sprint-budget-estimation-skill/SKILL.md` — bütçe tahmini
- `provider-cost-tracking-skill/SKILL.md` — maliyet takibi
