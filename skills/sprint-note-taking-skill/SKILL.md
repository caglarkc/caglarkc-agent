---
name: sprint-note-taking
description: Planner AI için — sprint boyunca önemli gözlemleri, kararları ve öğrenilen dersleri kısa notlar olarak kaydetmek.
---

## Purpose

Sprint sırasında alınan küçük kararlar sonradan unutulur.
"Neden bu dosyayı yazmaktan vazgeçtik?" sorusu cevapsız kalır.
Notlar, sprint sonunda özet üretimini kolaylaştırır.

---

## When to Apply

- Sprint sırasında önemli bir karar alındığında
- Beklenmedik bir sorunla karşılaşıldığında
- Gelecek sprint için not bırakılmak istendiğinde
- Kullanıcı "bunu not et" dediğinde

---

## Rules

- Not: kısa (1-3 cümle), zamanlamalı (timestamp).
- Not türleri: observation, decision, blocker, lesson.
- Notlar `sprint_notes` tablosunda veya state'de saklanır.
- Sprint özeti oluşturulurken notlar dahil edilir.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SprintNote:
    sprint_id: str
    note_type: str  # "observation" | "decision" | "blocker" | "lesson"
    content: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    note_id: str = field(
        default_factory=lambda: str(uuid.uuid4())[:8]
    )

def add_sprint_note(
    state: OrchestratorState,
    note_type: str,
    content: str,
) -> dict:
    notes = list(state.get("sprint_notes", []))
    note = SprintNote(
        sprint_id=state.get("sprint_id", ""),
        note_type=note_type,
        content=content,
    )
    notes.append({
        "note_id": note.note_id,
        "type": note_type,
        "content": content,
        "ts": note.created_at.isoformat(),
    })
    return {"sprint_notes": notes}

def format_sprint_notes(notes: list[dict]) -> str:
    if not notes:
        return ""
    lines = ["Sprint Notları:"]
    for note in notes:
        ts = note["ts"][:16]
        lines.append(f"  [{note['type'].upper()}] {ts}: {note['content']}")
    return "\n".join(lines)
```

PM not alma:
```
[SOHBET] Not alındı:

[DECISION] 14:23: Telegram yerine CLI onay kullanıldı 
(Telegram token test ortamında mevcut değil)

Sprint sonu özetine eklenecek.
```

---

## References

- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
- `sprint-summary-generation-skill/SKILL.md` — sprint özeti
- `technical-debt-logging-skill/SKILL.md` — teknik borç notu
