---
name: structured-logging-context
description: Coder AI için — log kayıtlarına yapısal bağlam (sprint_id, worker_id, task_id) eklemek; filtrelenebilir log üretmek.
---

## Purpose

Düz metin log analize gelmiyor — hangi sprint, hangi worker bilinmiyor.
Yapısal log: JSON formatında, her satır ayrıştırılabilir.
sprint_id ile filtrele: tek sprint'in tüm logları bir arada.

---

## When to Apply

- LangGraph node'larında log yazılırken
- Worker veya executor hata loglarında
- Log aggregation (ELK, Loki) entegrasyonu yapılırken

---

## Rules

- Format: JSON (production) veya renkli metin (development).
- Zorunlu alanlar: timestamp, level, message, sprint_id.
- Opsiyonel: worker_id, task_id, file_path.
- Exception: traceback yapısal alanda saklanır.

---

## Guidelines

```python
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def __init__(self, extra_fields: dict | None = None):
        super().__init__()
        self._extra = extra_fields or {}
    
    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "ts":      datetime.utcnow().isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
            **self._extra,
        }
        # contextvars'tan sprint/worker bilgisi
        ctx = _get_log_context()
        if ctx:
            log_dict.update(ctx)
        
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_dict, ensure_ascii=False)

import contextvars

_log_ctx: contextvars.ContextVar[dict] = contextvars.ContextVar("log_ctx", default={})

def set_log_context(**kwargs) -> None:
    current = dict(_log_ctx.get())
    current.update(kwargs)
    _log_ctx.set(current)

def _get_log_context() -> dict:
    return _log_ctx.get()

def get_sprint_logger(sprint_id: str, worker_id: str | None = None) -> logging.Logger:
    set_log_context(sprint_id=sprint_id, worker_id=worker_id or "")
    logger = logging.getLogger(f"sprint.{sprint_id}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
    return logger
```

---

## References

- `logging-patterns-skill/SKILL.md` — loglama kalıpları
- `telemetry-logging-skill/SKILL.md` — telemetri loglama
- `node-error-boundary-skill/SKILL.md` — node hata sınırı
