---
name: sprint-observability
description: Planner AI için — sprint sistemine gözlemlenebilirlik eklemek; metrik, log ve trace üçgenini kurarak sorunları hızlı tespit etmek.
---

## Purpose

"Neden yavaş?" sorusu metricsiz yanıtsız kalır.
Gözlemlenebilirlik: metrik (sayı), log (olay) ve trace (akış) birlikte anlam taşır.
Sorun anında hangi node, kaç ms, hangi hata — anlık görünür.

---

## When to Apply

- Production sprint sistemi kurulurken
- Performans sorunu araştırılırken
- SLA/SLO tanımlanacak olduğunda

---

## Rules

- Metrik: Prometheus formatı veya basit sayaç dict.
- Log: yapısal JSON (structured-logging-context ile).
- Trace: span_id ile LangGraph node'larını izle.
- Dashboard: Grafana veya basit terminal çıktısı.

---

## Guidelines

```python
import time
from contextlib import asynccontextmanager
from collections import defaultdict
from typing import AsyncIterator

class SprintMetrics:
    def __init__(self):
        self._counters: dict[str, int]   = defaultdict(int)
        self._timers:   dict[str, list]  = defaultdict(list)

    def increment(self, key: str, value: int = 1) -> None:
        self._counters[key] += value

    def record_duration(self, key: str, seconds: float) -> None:
        self._timers[key].append(seconds)

    def get_counter(self, key: str) -> int:
        return self._counters[key]

    def get_avg_duration(self, key: str) -> float:
        vals = self._timers.get(key, [])
        return sum(vals) / len(vals) if vals else 0.0

    def summary(self) -> dict:
        return {
            "counters": dict(self._counters),
            "avg_durations": {k: round(self.get_avg_duration(k), 3) for k in self._timers},
        }

_metrics = SprintMetrics()

@asynccontextmanager
async def timed_operation(name: str) -> AsyncIterator[None]:
    start = time.monotonic()
    _metrics.increment(f"{name}.calls")
    try:
        yield
        _metrics.increment(f"{name}.success")
    except Exception:
        _metrics.increment(f"{name}.errors")
        raise
    finally:
        elapsed = time.monotonic() - start
        _metrics.record_duration(name, elapsed)

# Kullanım
async def worker_node_traced(state: dict) -> dict:
    async with timed_operation("worker_node"):
        result = await _do_work(state)
    return result

def get_observability_report() -> str:
    s = _metrics.summary()
    lines = ["Observability Report:"]
    for k, v in s["counters"].items():
        avg = s["avg_durations"].get(k.replace(".calls", ""), 0)
        lines.append(f"  {k}: {v}" + (f" (avg {avg:.3f}s)" if avg else ""))
    return "\n".join(lines)
```

---

## References

- `telemetry-logging-skill/SKILL.md` — telemetri
- `structured-logging-context-skill/SKILL.md` — yapısal loglama
- `sprint-metrics-collection-skill/SKILL.md` — metrik toplama
