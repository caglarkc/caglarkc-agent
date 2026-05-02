---
name: constant-and-config-extraction
description: Coder AI için — sihirli sayı ve string'leri koddan çıkarıp sabit veya config olarak tanımlamak; bakımı kolaylaştırmak.
---

## Purpose

Kodda `3`, `"planned"`, `0.7` gibi değerler tekrar ederse bakım zorlaşır.
Sabit değiştirilmek istendiğinde tüm dosya taranmak zorunda kalınır.
Merkezi sabitler tek noktadan değiştirmeyi sağlar.

---

## When to Apply

- Aynı sayı veya string birden fazla yerde kullanılırken
- Timeout, retry sayısı, model adı gibi konfigürasyon değerleri kodlanırken
- `src/core/constants.py` veya `src/config/settings.py` düzenlenirken

---

## Rules

- Sayısal sabitler: `MAX_RETRIES = 3` formatında büyük harf.
- String sabitler: aynı kural.
- Uygulama geneli config: `Settings` Pydantic modeli.
- Node-lokal sabitler: dosya başında tanımlanabilir.
- `"magic"` sayı = yorumsuz, isimsiz sayısal literal — yasak.

---

## Guidelines

```python
# src/core/constants.py
MAX_RETRIES = 3
MAX_CONCURRENT_WORKERS = 3
CHECKPOINT_DB_PATH = "graph_checkpoint.db"
FILE_STATUS_PLANNED = "planned"
FILE_STATUS_RESERVED = "reserved"
FILE_STATUS_IN_PROGRESS = "in_progress"
FILE_STATUS_DONE = "done"
FILE_STATUS_FAILED = "failed"
DEFAULT_LLM_TEMPERATURE = 0.2
RETRY_BASE_DELAY = 2.0   # saniye
```

Settings Pydantic modeli:
```python
# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "codellama:13b"
    openrouter_api_key: str = ""
    telegram_bot_token: str = ""
    db_path: str = "caglarkc_agent.db"
    checkpoint_db_path: str = "graph_checkpoint.db"
    max_concurrent_workers: int = 3
    max_retries: int = 3

    class Config:
        env_file = ".env"

settings = Settings()
```

Kullanım:
```python
from src.config.settings import settings
from src.core.constants import MAX_RETRIES, FILE_STATUS_DONE
```

---

## References

- `code-mode-skill/SKILL.md` — genel kurallar
- `settings-validation-skill/SKILL.md` — settings doğrulama
- `aiosqlite-patterns-skill/SKILL.md` — DB path kullanımı
