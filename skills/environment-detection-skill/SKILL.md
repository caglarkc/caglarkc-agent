---
name: environment-detection
description: Coder AI için — uygulamanın hangi ortamda çalıştığını (development/test/production) tespit etmek; ortama göre farklı davranış sergilemek.
---

## Purpose

Test ortamında gerçek Telegram mesajı gönderilmez.
Production'da debug log açılmaz.
Ortam tespiti bu farklılıkları otomatik yönetir.

---

## When to Apply

- Ortama bağlı davranış (log seviyesi, bildirim, DB yolu) implemente edilirken
- Test ortamında gerçek harici servis çağrısını önlerken
- `Settings` sınıfına ortam alanı eklenirken

---

## Rules

- `ENVIRONMENT` env var: `"development"` | `"test"` | `"production"`.
- Test ortamı: gerçek LLM çağrısı yapılmaz.
- Production: debug log kapalı, gerçek bildirimler aktif.
- Development: tüm özellikler aktif, verbose log.

---

## Guidelines

```python
import os
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"

def get_environment() -> Environment:
    env = os.environ.get("ENVIRONMENT", "development").lower()
    try:
        return Environment(env)
    except ValueError:
        return Environment.DEVELOPMENT

def is_test() -> bool:
    return get_environment() == Environment.TEST

def is_production() -> bool:
    return get_environment() == Environment.PRODUCTION

# Settings'te ortam bazlı varsayılanlar
class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    
    @property
    def log_level(self) -> str:
        if self.environment == Environment.PRODUCTION:
            return "INFO"
        return "DEBUG"
    
    @property
    def use_real_llm(self) -> bool:
        return self.environment != Environment.TEST
    
    @property
    def send_notifications(self) -> bool:
        return self.environment == Environment.PRODUCTION

# Ortam bazlı LLM seçimi
def create_llm(settings: Settings) -> BaseChatModel:
    if not settings.use_real_llm:
        return MockLLM()   # test ortamı
    return create_planner_llm(settings)
```

pytest konfigürasyonu:
```toml
[tool.pytest.ini_options]
env = ["ENVIRONMENT=test"]
```

---

## References

- `settings-validation-skill/SKILL.md` — settings
- `env-file-setup-skill/SKILL.md` — env dosyası
- `dependency-injection-patterns-skill/SKILL.md` — DI
