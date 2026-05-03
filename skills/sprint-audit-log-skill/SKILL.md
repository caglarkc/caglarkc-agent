---
name: sprint-audit-log
description: Planner AI için — sprint boyunca yapılan tüm kritik işlemleri değiştirilemez denetim kaydına yazmak.
---

## Purpose

"Kim ne zaman ne yaptı?" sorusu yanıtsız kalmamalı.
Denetim logu: plan oluşturma, onay, görev durumu değişimleri, hata gibi olayları zaman damgalı kaydeder.
Uyumluluk, hata ayıklama ve retrospective için temel kaynak.

---

## When to Apply

- Sprint başlatıldığında
- Onay alındığında veya reddedildiğinde
- Görev durumu değiştiğinde
- Hata veya abort olduğunda

---

## Rules

- Kayıt: append-only — güncelleme yok, silme yok.
- Her kayıt: event_type, actor, timestamp, payload.
- Depolama: SQLite `audit_log` tablosu veya JSONL dosyası.
- Erişim: sadece okuma — state düzeltmesi bu tablodan yapılmaz.

---

## Guidelines

```python
import json
from datetime import datetime
from pathlib import Path

AUDIT_LOG_PATH = "logs/audit.jsonl"

def write_audit_event(
    event_type: str,
    actor: str,
    payload: dict,
    log_path: str = AUDIT_LOG_PATH,
) -> None:
    record = {
        "ts":         datetime.utcnow().isoformat(),
        "event_type": event_type,
        "actor":      actor,
        "payload":    payload,
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def read_audit_log(
    log_path: str = AUDIT_LOG_PATH,
    sprint_id: str | None = None,
) -> list[dict]:
    path = Path(log_path)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
            if sprint_id is None or r.get("payload", {}).get("sprint_id") == sprint_id:
                records.append(r)
        except json.JSONDecodeError:
            pass
    return records

AUDIT_EVENTS = {
    "sprint.created":  ("planner",  lambda s: {"sprint_id": s.get("sprint_id"), "goal": s.get("sprint_goal")}),
    "sprint.approved": ("user",     lambda s: {"sprint_id": s.get("sprint_id")}),
    "task.done":       ("worker",   lambda t: {"task_id": t.get("id"), "file": t.get("file_path")}),
    "sprint.aborted":  ("system",   lambda s: {"sprint_id": s.get("sprint_id"), "reason": s.get("abort_reason")}),
}
```

---

## References

- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
- `structured-logging-context-skill/SKILL.md` — yapısal loglama
- `telemetry-logging-skill/SKILL.md` — telemetri
