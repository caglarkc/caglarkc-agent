---
name: sprint-knowledge-base
description: Planner AI için — sprint boyunca öğrenilen teknik bilgileri, çözülen sorunları ve en iyi pratikleri erişilebilir bir bilgi tabanında saklamak.
---

## Purpose

Aynı sorun tekrar tekrar çözülür çünkü ilk çözüm yazılmadı.
Bilgi tabanı: sprint çıktılarından öğrenilen her şeyi aranabilir saklar.
Bir sonraki sprint plancısı: "Bu sorun daha önce nasıl çözüldü?" diye sorabilir.

---

## When to Apply

- Sprint sırasında teknik sorun çözüldüğünde
- Önemli mimari karar alındığında
- Kullanıcı "bunu not et, ileride kullanalım" dediğinde

---

## Rules

- Kayıt: başlık, içerik, etiketler, kaynak sprint ID.
- Arama: tam metin veya etiket bazlı.
- Max kayıt: 200 (eski kayıtlar arşivlenir).
- Format: markdown, kod örnekleriyle.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class KnowledgeEntry:
    title:     str
    content:   str
    tags:      list[str]
    sprint_id: str
    entry_id:  str = field(default_factory=lambda: str(__import__("uuid").uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class KnowledgeBase:
    def __init__(self, max_entries: int = 200):
        self._entries: list[KnowledgeEntry] = []
        self._max = max_entries

    def add(self, title: str, content: str, tags: list[str], sprint_id: str) -> KnowledgeEntry:
        if len(self._entries) >= self._max:
            self._entries.pop(0)
        entry = KnowledgeEntry(title=title, content=content, tags=tags, sprint_id=sprint_id)
        self._entries.append(entry)
        return entry

    def search(self, query: str) -> list[KnowledgeEntry]:
        q = query.lower()
        return [
            e for e in self._entries
            if q in e.title.lower() or q in e.content.lower()
            or any(q in tag.lower() for tag in e.tags)
        ]

    def get_by_tag(self, tag: str) -> list[KnowledgeEntry]:
        return [e for e in self._entries if tag in e.tags]

    def to_prompt_context(self, query: str, max_entries: int = 3) -> str:
        results = self.search(query)[:max_entries]
        if not results:
            return ""
        lines = ["İlgili bilgi tabanı kayıtları:"]
        for e in results:
            lines.append(f"\n### {e.title}")
            lines.append(e.content[:300])
        return "\n".join(lines)
```

---

## References

- `planner-memory-skill/SKILL.md` — planner belleği
- `sprint-note-taking-skill/SKILL.md` — sprint notları
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
