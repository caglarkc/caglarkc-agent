---
name: logging-usage-review
description: Planner AI için — log seviyelerinin doğru kullanıldığını, API key gibi hassas verinin log'a düşmediğini ve log mesajlarının yeterince bilgi içerdiğini review sırasında kontrol etmek.
---

## Purpose

Log kalitesini review sırasında garantiler.
Yanlış log seviyesi hem noise hem de kritik bilgi kaybına yol açar.
API key, token gibi hassas veriyi log'a düşürmemek güvenlik gereğidir.

---

## When to Apply

- `logger.*` çağrısı içeren her kod review'ında
- Hata handling kodu review edilirken
- Yeni servis veya node eklenirken

---

## Rules

- `DEBUG`: Detaylı geliştirme bilgisi (payload, state dump). Production'da kapalı.
- `INFO`: Normal operasyon akışı (sprint başladı, worker atandı).
- `WARNING`: Beklenmedik ama kurtarılabilir durum (rate limit, fallback'e geçildi).
- `ERROR`: Operasyon başarısız oldu ama sistem çalışıyor (worker failed).
- `CRITICAL`: Sistem çalışamaz hale geldi (checkpoint corrupt, DB erişilemiyor).
- API key, token, şifre log'a yazılmaz — maskelenir.
- `logger.exception()` exception handling içinde kullanılır (stack trace otomatik eklenir).

---

## Guidelines

Seviye kullanımı:
```python
# DEBUG — geliştirme sırasında
logger.debug(f"LLM prompt: {prompt[:100]}...")

# INFO — normal akış
logger.info(f"Sprint {sprint_id} başlatıldı", extra={"project_id": project_id})

# WARNING — beklenmedik ama çalışıyor
logger.warning(f"Ollama yanıt vermedi, OpenRouter'a geçildi")

# ERROR — operasyon başarısız
logger.error(f"Worker {worker_id} başarısız: {error}", extra={"retry_count": count})

# CRITICAL — sistem durdu
logger.critical(f"Checkpoint DB bozuldu: {db_path}")
```

Hassas veri maskeleme:
```python
# YANLIŞ
logger.info(f"OpenRouter API key: {api_key}")

# DOĞRU
logger.info(f"OpenRouter API key: {api_key[:8]}...{api_key[-4:]}")

# Daha iyi — key hiç log'a girmesin
logger.info("OpenRouter bağlantısı başarılı", extra={"model": model_name})
```

`extra` context pattern:
```python
# Structured context ile log (grep edilebilir)
logger.info(
    "Dosya yazıldı",
    extra={
        "project_id": project_id,
        "file_path": target_file,
        "worker_id": worker_id,
        "duration_ms": elapsed
    }
)
```

---

## References

- `exception-handling-review-skill/SKILL.md` — hata log'lama
- `api-key-masking-skill/SKILL.md` — güvenli log
- `structured-error-logging-skill/SKILL.md` — structured log
