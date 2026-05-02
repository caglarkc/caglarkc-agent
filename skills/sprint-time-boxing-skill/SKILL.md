---
name: sprint-time-boxing
description: Planner AI için — sprint'e sabit süre sınırı koymak; süre dolduğunda tamamlanmamış görevleri gelecek sprinte ertelemek.
---

## Purpose

Sınırsız sprint bitmez veya çok uzar.
Time-boxing: sprint başlarken max süre belirlenir.
Süre dolduğunda: tamamlananlar kabul, kalanlar backlog'a.

---

## When to Apply

- Sprint başlatılırken süre sınırı isteniyor
- Kullanıcı "1 saatte ne kadar yapabilirsin?" diye sorduğunda
- CI/CD'de sabit pencere (scheduled sprint) kullanılırken

---

## Rules

- Varsayılan time-box: 60 dakika.
- Uyarı: kalan 10 dakikada bildir.
- Süre dolunca: aktif görev tamamlanır, yenisi başlatılmaz.
- Raporlama: tamamlanan vs. ertelenen görev sayısı.

---

## Guidelines

```python
import asyncio
from datetime import datetime, timedelta

class SprintTimer:
    def __init__(self, duration_minutes: float = 60.0):
        self._duration = duration_minutes
        self._start: datetime | None = None
    
    def start(self) -> None:
        self._start = datetime.utcnow()
    
    @property
    def elapsed_minutes(self) -> float:
        if not self._start:
            return 0.0
        return (datetime.utcnow() - self._start).total_seconds() / 60
    
    @property
    def remaining_minutes(self) -> float:
        return max(0.0, self._duration - self.elapsed_minutes)
    
    @property
    def is_expired(self) -> bool:
        return self.elapsed_minutes >= self._duration
    
    @property
    def deadline(self) -> datetime | None:
        return (self._start + timedelta(minutes=self._duration)) if self._start else None

async def run_time_boxed_sprint(
    sprint_coroutine,
    duration_minutes: float,
    warn_at_minutes: float = 10.0,
) -> dict:
    timer = SprintTimer(duration_minutes)
    timer.start()
    
    async def warn_task():
        await asyncio.sleep((duration_minutes - warn_at_minutes) * 60)
        print(f"⚠️ Sprint bitimine {warn_at_minutes:.0f} dakika kaldı!")
    
    warning = asyncio.create_task(warn_task())
    
    try:
        result = await asyncio.wait_for(
            sprint_coroutine,
            timeout=duration_minutes * 60,
        )
        warning.cancel()
        return {**result, "time_boxed": False, "elapsed": timer.elapsed_minutes}
    except asyncio.TimeoutError:
        warning.cancel()
        return {
            "time_boxed": True,
            "elapsed":    timer.elapsed_minutes,
            "message":    f"Süre doldu ({duration_minutes:.0f} dk). Kalan görevler ertelendi.",
        }
```

---

## References

- `sprint-resource-limits-skill/SKILL.md` — kaynak sınırları
- `sprint-pause-resume-skill/SKILL.md` — duraklama/devam
- `sprint-cancellation-skill/SKILL.md` — sprint iptal
