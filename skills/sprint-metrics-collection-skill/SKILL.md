---
name: sprint-metrics-collection
description: Planner AI için — sprint boyunca üretilen kod kalitesi, süre ve hata oranı gibi metrikleri toplamak; iyileştirme kararlarına veri sağlamak.
---

## Purpose

Metricsiz iyileştirme rastgeledir.
Sprint sonunda temel metrikler toplanırsa eğilimler görülür.
"Worker hata oranı artıyor" tespiti provider değişikliğini tetikler.

---

## When to Apply

- Sprint tamamlandığında otomatik metrik hesaplanırken
- Periyodik rapor oluşturulurken
- Provider veya model değişikliğinin etkisi ölçülürken

---

## Rules

- Metrikler: süre, dosya sayısı, hata oranı, retry sayısı, review döngüsü.
- Depolama: `sprint_metrics` tablosu (ayrı tablo veya `sprints` JSON alan).
- Kullanıcıya özetlenir — ham veri değil.
- Trend: son 5 sprint ortalaması.

---

## Guidelines

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SprintMetrics:
    sprint_id: str
    total_files: int
    done_files: int
    failed_files: int
    total_duration_seconds: float
    retry_count: int
    review_cycles: int
    success_rate: float  # done / total

def calculate_sprint_metrics(
    state: OrchestratorState,
    start_time: datetime,
    end_time: datetime,
) -> SprintMetrics:
    registry = state.get("file_registry", {})
    total = len(registry)
    done = sum(1 for s in registry.values() if s == "done")
    failed = sum(1 for s in registry.values() if s == "failed")
    
    return SprintMetrics(
        sprint_id=state["sprint_id"],
        total_files=total,
        done_files=done,
        failed_files=failed,
        total_duration_seconds=(end_time - start_time).total_seconds(),
        retry_count=state.get("total_retries", 0),
        review_cycles=state.get("review_count", 0),
        success_rate=done / total if total > 0 else 0.0,
    )

# PM özet formatı
def format_metrics_summary(metrics: SprintMetrics) -> str:
    duration_min = metrics.total_duration_seconds / 60
    return (
        f"Sprint Metrikleri:\n"
        f"  Süre: {duration_min:.1f} dakika\n"
        f"  Başarı oranı: {metrics.success_rate:.0%}\n"
        f"  Dosya: {metrics.done_files}/{metrics.total_files}\n"
        f"  Review döngüsü: {metrics.review_cycles}\n"
    )
```

---

## References

- `progress-report-generation-skill/SKILL.md` — ilerleme raporu
- `sprint-completion-celebration-skill/SKILL.md` — tamamlanma
- `decision-log-maintenance-skill/SKILL.md` — kayıt
