---
name: settings-validation
description: Coder AI için — uygulama başlarken zorunlu environment variable'ların mevcut ve geçerli olduğunu doğrulamak; eksik config'i erken bildirmek.
---

## Purpose

Uygulama yarı çalışırken `TELEGRAM_BOT_TOKEN` eksik olduğu fark edilirse kötü deneyim olur.
Startup validation, eksik config'i daemon başlamadan raporlar.
`pydantic-settings` bu doğrulamayı otomatik yapar.

---

## When to Apply

- `Settings` sınıfı oluşturulurken
- Yeni zorunlu config alanı eklenirken
- `main.py` veya `daemon.py` startup kontrolü yazılırken

---

## Rules

- Zorunlu alan: `default` değeri olmadan tanımlanır.
- Opsiyonel alan: `default=""` veya `default=None`.
- `model_validator` ile çapraz alan doğrulaması yapılabilir.
- Doğrulama hatası: startup'ta `sys.exit(1)` ile sonlanır.
- `.env` dosyası: production'da gerçek değerler, test'te mock.

---

## Guidelines

```python
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator

class Settings(BaseSettings):
    # Zorunlu
    gemini_api_key: str
    db_path: str
    
    # Opsiyonel (default var)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "codellama:13b"
    openrouter_api_key: str = ""
    telegram_bot_token: str = ""
    max_concurrent_workers: int = 3
    log_level: str = "INFO"

    @field_validator("max_concurrent_workers")
    @classmethod
    def validate_workers(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("max_concurrent_workers 1-10 arasında olmalı")
        return v

    @model_validator(mode="after")
    def validate_provider_config(self) -> "Settings":
        if not self.ollama_base_url and not self.openrouter_api_key:
            raise ValueError(
                "En az bir LLM provider yapılandırılmalı: "
                "OLLAMA_BASE_URL veya OPENROUTER_API_KEY"
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Startup doğrulama
def validate_startup_config() -> Settings:
    try:
        return Settings()
    except Exception as e:
        print(f"Konfigürasyon hatası: {e}")
        sys.exit(1)
```

---

## References

- `constant-and-config-extraction-skill/SKILL.md` — sabitler
- `code-mode-skill/SKILL.md` — genel kurallar
- `provider-fallback-chain-skill/SKILL.md` — provider config
