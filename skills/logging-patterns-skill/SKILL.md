---
name: logging-patterns
description: Coder AI için — structlog veya standart logging ile tutarlı log mesajları yazmak; debug, info, warning, error seviyelerini doğru kullanmak.
---

## Purpose

Tutarsız log'lar prodüksiyon debugını zorlaştırır.
Structured logging, log'ları programatik olarak filtrelemeyi sağlar.
Log seviyesi yanlış kullanılırsa önemli hatalar gömülür.

---

## When to Apply

- Her yeni modül yazılırken (`logger = logging.getLogger(__name__)`)
- Node ve servis metodlarında işlem başlangıç/bitiş loglanırken
- Hata durumlarında exception loglanırken

---

## Rules

- Her modül başında: `logger = logging.getLogger(__name__)`
- `DEBUG`: geliştirme detayları — prodüksiyonda kapalı.
- `INFO`: önemli işlem adımları (sprint başladı, dosya yazıldı).
- `WARNING`: beklenmedik ama tolere edilebilir durum.
- `ERROR`: işlem başarısız, müdahale gerekebilir.
- Exception loglarken `logger.exception()` kullan — stack trace otomatik eklenir.

---

## Guidelines

```python
import logging

logger = logging.getLogger(__name__)

# Doğru seviye kullanımı
logger.debug(f"LLM prompt gönderiliyor: {len(messages)} mesaj")
logger.info(f"Sprint oluşturuldu: {sprint_id}")
logger.warning(f"Provider başarısız, fallback deneniyor: {provider_name}")
logger.error(f"Dosya yazılamadı: {file_path}")
logger.exception(f"Beklenmedik hata: {task_id}")  # stack trace ekler

# Structured context (key=value formatı)
logger.info(
    "Worker tamamlandı",
    extra={
        "worker_id": worker_id,
        "file_path": file_path,
        "duration_ms": elapsed_ms,
    }
)
```

Logging konfigürasyonu (main.py):
```python
import logging

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Gürültülü kütüphaneleri sustur
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
```

---

## References

- `code-mode-skill/SKILL.md` — genel kurallar
- `error-handling-patterns-skill/SKILL.md` — hata yönetimi
- `technical-debt-logging-skill/SKILL.md` — teknik borç logu
