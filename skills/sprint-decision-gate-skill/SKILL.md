---
name: sprint-decision-gate
description: Planner AI için — sprint belirli bir noktaya geldiğinde devam/dur kararını verilen kriterlere göre otomatik almak.
---

## Purpose

Her adımda kullanıcı sormak yerine önceden belirlenmiş kurallar devam/dur der.
Decision gate: sprint belirli bir eşiği geçince kriterlere bakılır.
Kriterleri karşılamıyorsa dur ve bildir, karşılıyorsa devam et.

---

## When to Apply

- Sprint ilerlerken otomatik kontrol noktaları tanımlanırken
- Hata oranı belirli eşiği geçtiğinde otomatik durdurma için
- CI/CD pipeline'ında kalite kapıları kurulurken

---

## Rules

- Gate: bir veya birden fazla kriter.
- Kriter türleri: hata oranı, süre, başarı yüzdesi, token limiti.
- Geçti: sprint devam eder.
- Geçemedi: sprint duraklar, kullanıcı bilgilendirilir, onay beklenir.

---

## Guidelines

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class GateCriterion:
    name:       str
    check_fn:   Callable[[dict], bool]
    blocking:   bool = True
    message:    str  = ""

def build_default_gates() -> list[GateCriterion]:
    return [
        GateCriterion(
            name="error_rate",
            check_fn=lambda s: _error_rate(s) < 0.5,
            blocking=True,
            message="Hata oranı %50'yi aştı — sprint durduruluyor",
        ),
        GateCriterion(
            name="token_budget",
            check_fn=lambda s: s.get("tokens_used", 0) < s.get("max_tokens", 500_000),
            blocking=True,
            message="Token bütçesi aşıldı",
        ),
        GateCriterion(
            name="time_limit",
            check_fn=lambda s: _elapsed_minutes(s) < s.get("sprint_minutes", 60),
            blocking=False,
            message="Sprint süresi doldu",
        ),
    ]

def _error_rate(state: dict) -> float:
    tasks = state.get("tasks", [])
    if not tasks:
        return 0.0
    failed = sum(1 for t in tasks if t.get("status") == "failed")
    return failed / len(tasks)

def _elapsed_minutes(state: dict) -> float:
    from datetime import datetime
    started = state.get("sprint_started_at")
    if not started:
        return 0.0
    return (datetime.utcnow() - datetime.fromisoformat(started)).total_seconds() / 60

def evaluate_gates(
    state: dict,
    gates: list[GateCriterion],
) -> tuple[bool, list[str]]:
    failures = []
    for gate in gates:
        if not gate.check_fn(state):
            failures.append(gate.message or gate.name)
            if gate.blocking:
                return False, failures
    return len([g for g in gates if not g.check_fn(state) and g.blocking]) == 0, failures
```

---

## References

- `sprint-approval-gate-skill/SKILL.md` — onay kapısı
- `sprint-abort-on-critical-failure-skill/SKILL.md` — kritik hata iptali
- `sprint-resource-limits-skill/SKILL.md` — kaynak sınırları
