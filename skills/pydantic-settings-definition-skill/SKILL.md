---
name: pydantic-settings-definition
description: Coder AI için — BaseSettings ile .env tabanlı konfigürasyon tanımlamanın bu projedeki doğru yolu; yeni alan ekleme, computed property ve validation.
---

## Purpose

`src/config/settings.py`'e yeni ayar alanı eklemenin standart yolunu sağlar.
.env dosyasından okuma, tip doğrulama ve varsayılan değer yönetimini birleştirir.
API key gibi hassas alanları güvenli yönetir.

---

## When to Apply

- Yeni dış servis veya konfigürasyona ihtiyaç duyulduğunda
- `src/config/settings.py`'e alan eklenirken
- `.env.example` güncellenmesi gerektiğinde

---

## Rules

- `from pydantic_settings import BaseSettings, SettingsConfigDict` kullanılır.
- `.env` dosyası `env_file=".env"` ile otomatik okunur.
- Zorunlu alanlar (API key gibi): default değer yok.
- Opsiyonel alanlar: default değer verilir.
- Hassas alanlar: `SecretStr` tipiyle tanımlanır.
- Computed property: `@property` ile tanımlanır.
- Singleton: `@lru_cache` ile tek instance.

---

## Guidelines

Settings tanımı:
```python
from functools import lru_cache
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # bilinmeyen env var'ları hata vermez
    )
    
    # Uygulama
    APP_NAME: str = "ai-orchestrator"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Veri yolları
    DATA_DIR: Path = Path("data")
    PROJECTS_ROOT: Path = Path("projects")
    
    # Zorunlu API key'ler
    GEMINI_API_KEY: SecretStr  # SecretStr ile log'a düşmez
    
    # Opsiyonel
    OPENROUTER_API_KEY_PRIMARY: SecretStr | None = None
    TELEGRAM_BOT_TOKEN: SecretStr | None = None
    
    # Computed properties
    @property
    def sqlite_db_path(self) -> Path:
        return self.DATA_DIR / "orchestrator.db"
    
    @property
    def graph_checkpoint_path(self) -> str:
        return str(self.DATA_DIR / "graph_checkpoint.db")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Yeni alan ekleme adımları:
1. `settings.py`'e alan ekle
2. `.env.example`'a örnek değer ekle
3. Gerekiyorsa `RUNBOOK.md`'ye not düş

---

## References

- `env-var-validation-skill/SKILL.md` — zorunlu env kontrolü
- `api-key-masking-skill/SKILL.md` — SecretStr kullanımı
- `project-architecture-skill/SKILL.md` — config katmanı
