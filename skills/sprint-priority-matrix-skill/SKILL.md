---
name: sprint-priority-matrix
description: Planner AI için — birden fazla bekleyen özellik isteği varsa önceliklendirme matrisiyle hangi sprint'in önce yapılacağına karar vermek.
---

## Purpose

5 farklı özellik isteği varken hangisinden başlanacağı bilinmezse plan yapılamaz.
Önceliklendirme matrisi: etki × çaba kombinasyonuyla sıralar.
Yüksek etki + düşük çaba = önce yapılır.

---

## When to Apply

- Birden fazla bekleyen sprint isteği varken
- Roadmap sıralaması yapılırken
- Kullanıcı "önce neyi yapayım?" diye sorduğunda

---

## Rules

- Etki: iş değeri (1-5).
- Çaba: sprint büyüklüğü S/M/L → 1/2/3.
- Skor: etki / çaba (yüksek = önce).
- Bağımlılık kısıtı: bağımlı sprint skor ne olursa olsun sonra yapılır.
- Kullanıcı sıralamasını override edebilir.

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class SprintCandidate:
    title: str
    impact: int        # 1-5
    effort: int        # 1 (S), 2 (M), 3 (L)
    depends_on: str | None = None
    
    @property
    def priority_score(self) -> float:
        return self.impact / self.effort

def prioritize_sprints(
    candidates: list[SprintCandidate],
) -> list[SprintCandidate]:
    # Bağımlılıkları çöz
    independent = [c for c in candidates if not c.depends_on]
    dependent = [c for c in candidates if c.depends_on]
    
    # Bağımsız olanları sırala
    sorted_independent = sorted(
        independent,
        key=lambda c: c.priority_score,
        reverse=True,
    )
    
    # Bağımlı olanlar sona
    return sorted_independent + dependent
```

PM sunum formatı:
```
[PLANLAMA] Önceliklendirme matrisi:

1. Telegram onay (Etki:5, Çaba:M) — Skor: 2.5
   → Yüksek değer, orta çaba — ÖNERİLEN İLK

2. Repository testleri (Etki:4, Çaba:S) — Skor: 4.0
   → Hızlı tamamlanır, değerli

3. CLI refactor (Etki:2, Çaba:L) — Skor: 0.7
   → Düşük öncelik

Önerim: #2, #1, #3 sırasıyla
Ne düşünüyorsunuz?
```

---

## References

- `sprint-budget-estimation-skill/SKILL.md` — büyüklük
- `multi-sprint-roadmap-design-skill/SKILL.md` — roadmap
- `feature-breakdown-skill/SKILL.md` — özellik ayrıştırma
