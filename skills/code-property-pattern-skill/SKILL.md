---
name: code-property-pattern
description: Coder AI için — Python @property decorator ile hesaplanan özellik, doğrulama ve lazy loading uygulamak.
---

## Purpose

Direkt attribute erişimi sınırsız — geçersiz değer atanabilir.
`@property`: getter/setter'ı method gibi gizler, attribute syntax'ı korur.
Computed property, lazy init, readonly attr için temiz Python deyimi.

---

## When to Apply

- Hesaplanan özellik (mevcut alan kombinasyonu) tanımlanırken
- Attribute yazımında doğrulama gerektiğinde
- Lazy loading: ağır kaynak ilk erişimde yüklenirken

---

## Rules

- Property adı: snake_case, fiil yok (isim).
- Setter: yalnızca doğrulama gerektiren alanlarda.
- Lazy: `_cache` alanı None ise hesapla, değilse döndür.
- `__slots__` ile birlikte kullanımda dikkat.

---

## Guidelines

```python
from datetime import datetime

class SprintState:
    def __init__(self, tasks: list[dict], started_at: str | None = None):
        self._tasks     = tasks
        self._started   = started_at
        self._kpi_cache = None

    @property
    def completion_rate(self) -> float:
        total = len(self._tasks)
        if not total:
            return 0.0
        done = sum(1 for t in self._tasks if t.get("status") == "done")
        return done / total

    @property
    def elapsed_minutes(self) -> float:
        if not self._started:
            return 0.0
        delta = datetime.utcnow() - datetime.fromisoformat(self._started)
        return delta.total_seconds() / 60

    @property
    def kpi(self) -> dict:
        if self._kpi_cache is None:
            self._kpi_cache = {
                "completion": self.completion_rate,
                "elapsed":    self.elapsed_minutes,
            }
        return self._kpi_cache

    def invalidate_cache(self) -> None:
        self._kpi_cache = None

    @property
    def status(self) -> str:
        rate = self.completion_rate
        if rate >= 1.0:
            return "completed"
        elif rate > 0:
            return "in_progress"
        return "not_started"

    @status.setter
    def status(self, value: str) -> None:
        allowed = {"completed", "in_progress", "not_started", "failed", "cancelled"}
        if value not in allowed:
            raise ValueError(f"Geçersiz durum: {value}. İzin verilenler: {allowed}")
        self._explicit_status = value
```

---

## References

- `dataclass-vs-pydantic-skill/SKILL.md` — dataclass vs pydantic
- `type-narrowing-patterns-skill/SKILL.md` — tip daraltma
- `code-class-design-skill/SKILL.md` — sınıf tasarımı
