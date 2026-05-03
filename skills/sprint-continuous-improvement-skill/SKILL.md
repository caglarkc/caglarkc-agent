---
name: sprint-continuous-improvement
description: Planner AI için — her sprint döngüsünden elde edilen içgörülerle sistemi sürekli iyileştirmek; retrospective bulgularını otomatik uygulamak.
---

## Purpose

Tek seferlik retrospective unutulur — değişiklik olmaz.
Sürekli iyileştirme: her sprint sonunda ölçüm, analiz, küçük değişiklik.
Sprint 5 → Sprint 6: daha iyi tahminler, daha az retry, daha kısa süre.

---

## When to Apply

- Sprint tamamlandıktan sonra retrospective adımında
- 3+ sprint verisi birikince trend analizi yapılırken
- "Sistem nasıl daha iyi olur?" sorusu yanıtlanırken

---

## Rules

- Ölçüm: her sprint KPI otomatik hesaplanır.
- Analiz: önceki sprint ile kıyaslama.
- Değişiklik: küçük, tek, ölçülebilir.
- Etki: sonraki sprint bu değişiklikle çalışır.

---

## Guidelines

```python
from dataclasses import dataclass
from statistics import mean

@dataclass
class ImprovementAction:
    metric:      str
    direction:   str  # "increase" | "decrease"
    target:      float
    action:      str
    config_key:  str
    new_value:   object

def analyze_trends(sprint_history: list[dict]) -> list[ImprovementAction]:
    if len(sprint_history) < 3:
        return []

    actions = []
    recent = sprint_history[-3:]

    # Retry oranı yüksekse timeout artır
    retry_rates = []
    for s in recent:
        tasks = s.get("tasks", [])
        if tasks:
            retries = sum(t.get("retry_count", 0) for t in tasks)
            retry_rates.append(retries / len(tasks))
    if retry_rates and mean(retry_rates) > 1.5:
        actions.append(ImprovementAction(
            metric="avg_retries",
            direction="decrease",
            target=1.0,
            action="LLM timeout artırıldı — modele daha fazla süre verildi",
            config_key="llm_timeout",
            new_value=min(120.0, recent[-1].get("config", {}).get("llm_timeout", 60.0) * 1.2),
        ))

    # Tamamlanma oranı düşükse worker sayısı artır
    completion_rates = []
    for s in recent:
        tasks = s.get("tasks", [])
        if tasks:
            done = sum(1 for t in tasks if t.get("status") == "done")
            completion_rates.append(done / len(tasks))
    if completion_rates and mean(completion_rates) < 0.7:
        actions.append(ImprovementAction(
            metric="completion_rate",
            direction="increase",
            target=0.85,
            action="Görev tahmini çarpanı artırıldı",
            config_key="estimation_multiplier",
            new_value=1.3,
        ))

    return actions

def apply_improvements(config: dict, actions: list[ImprovementAction]) -> dict:
    updated = dict(config)
    for action in actions:
        updated[action.config_key] = action.new_value
    return updated
```

---

## References

- `sprint-feedback-loop-skill/SKILL.md` — geri besleme döngüsü
- `sprint-rollup-metrics-skill/SKILL.md` — rollup metrikleri
- `task-estimation-calibration-skill/SKILL.md` — tahmin kalibrasyonu
