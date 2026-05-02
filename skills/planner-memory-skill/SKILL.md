---
name: planner-memory
description: Planner AI için — kullanıcı tercihlerini, geçmiş kararları ve proje özelliklerini kısa vadeli bellekte tutmak.
---

## Purpose

Her konuşmada kullanıcı aynı şeyleri tekrar açıklamak zorunda kalır.
Planner belleği: önceki konuşmalardan öğrenilenleri saklar.
"Bu kullanıcı Telegram yerine CLI tercih ediyor" gibi bilgiler aktarılır.

---

## When to Apply

- Kullanıcı tercihini belirttiğinde (model, dil, format)
- Önceki sprintlerde alınan kararlar yeni sprintle ilgiliyken
- Kullanıcı "bunu hatırla" dediğinde

---

## Rules

- Bellek: key-value store, maks 50 kayıt.
- Kayıt: tercih türü + değer + oluşturma zamanı.
- Eskiyen kayıtlar (30+ gün) otomatik temizlenir.
- Hassas bilgi (API key, parola) belleğe alınmaz.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class MemoryEntry:
    key: str
    value: str
    category: str  # "preference" | "decision" | "project_fact"
    created_at: datetime = field(default_factory=datetime.utcnow)

class PlannerMemory:
    def __init__(self, max_entries: int = 50):
        self._store: dict[str, MemoryEntry] = {}
        self._max = max_entries
    
    def remember(self, key: str, value: str, category: str = "preference") -> None:
        if len(self._store) >= self._max:
            self._evict_oldest()
        self._store[key] = MemoryEntry(key, value, category)
    
    def recall(self, key: str) -> str | None:
        entry = self._store.get(key)
        return entry.value if entry else None
    
    def recall_all(self, category: str | None = None) -> dict[str, str]:
        return {
            k: e.value
            for k, e in self._store.items()
            if category is None or e.category == category
        }
    
    def forget(self, key: str) -> None:
        self._store.pop(key, None)
    
    def cleanup_old(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        old = [k for k, e in self._store.items() if e.created_at < cutoff]
        for k in old:
            del self._store[k]
        return len(old)
    
    def _evict_oldest(self) -> None:
        if self._store:
            oldest = min(self._store, key=lambda k: self._store[k].created_at)
            del self._store[oldest]
    
    def to_prompt_fragment(self) -> str:
        prefs = self.recall_all("preference")
        if not prefs:
            return ""
        lines = ["Kullanıcı tercihleri:"]
        for k, v in prefs.items():
            lines.append(f"  - {k}: {v}")
        return "\n".join(lines)
```

---

## References

- `conversation-history-trimming-skill/SKILL.md` — konuşma geçmişi
- `sprint-note-taking-skill/SKILL.md` — sprint notları
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
