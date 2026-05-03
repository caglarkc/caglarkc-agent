---
name: structured-error-logging
description: Coder AI için — hata log'larını `extra` dict ile yapılandırmak; grep edilebilir, izlenebilir ve context-rich log kayıtları oluşturmak.
---

## Purpose

Log'ların sadece mesaj değil, aranabilir context taşımasını sağlar.
`project_id`, `worker_id`, `file_path` gibi alanları `extra` dict ile log'a ekler.
Log aggregation sistemlerinde (ELK, Loki) filtrelenebilir log yapısı kurar.

---

## When to Apply

- Exception yakalandığında
- Önemli operasyon tamamlandığında (sprint bitti, worker tamamladı)
- Performance measurement yapılırken

---

## Rules

- Her log `extra` dict ile en az `project_id` taşır (varsa).
- Exception log'ları `logger.exception()` ile (stack trace otomatik).
- Performance log'ları `duration_ms` alanı içerir.
- Hassas veri `extra`'ya girmez (API key, token).
- Log seviyesi doğru seçilir (INFO/WARNING/ERROR/CRITICAL).

---

## Guidelines

Structured logging pattern'ları:
```python
import time

# Context ile INFO log
logger.info(
    "Sprint tamamlandı",
    extra={
        "project_id": project_id,
        "sprint_id": sprint_id,
        "files_written": len(completed_files),
        "review_cycles": review_cycles,
        "duration_ms": int((time.monotonic() - start_time) * 1000)
    }
)

# Worker context ile WARNING
logger.warning(
    "Provider fallback devreye girdi",
    extra={
        "project_id": project_id,
        "worker_id": worker_id,
        "failed_provider": "ollama",
        "fallback_provider": "openrouter_primary",
        "target_file": target_file
    }
)

# Exception ile ERROR
try:
    result = await llm_provider.generate(prompt)
except LLMTimeoutError as e:
    logger.error(
        f"LLM timeout: {e}",
        extra={
            "project_id": project_id,
            "worker_id": worker_id,
            "target_file": target_file,
            "attempt": attempt_count,
            "timeout_seconds": 30
        }
    )
    raise

# logger.exception — stack trace otomatik
except Exception as e:
    logger.exception(
        "Beklenmedik hata",
        extra={"project_id": project_id, "node": "planner"}
    )
```

---

## References

- `logging-usage-review-skill/SKILL.md` — log seviyesi
- `exception-handling-review-skill/SKILL.md` — exception handling
- `api-key-masking-skill/SKILL.md` — hassas veri
