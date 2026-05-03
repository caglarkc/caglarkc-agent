---
name: code-environment-guard
description: Coder AI için — üretilen kodun yanlış ortamda (production vs dev) çalışmasını engelleyen guard'lar eklemek.
---

## Purpose

Geliştirme kodu production'da yanlışlıkla çalışabilir.
Environment guard: `ENV` değişkenini kontrol eder, yanlış ortamda dur.
Debug endpoint, seed data, test fixture gibi şeyler production'a taşınmaz.

---

## When to Apply

- Debug veya test amaçlı kod yazılırken
- Seed/fixture fonksiyonları oluşturulurken
- Sadece dev'de çalışması gereken endpoint eklenirken

---

## Rules

- Guard: fonksiyon başında `ENV` kontrolü.
- Production'da yasak: debug endpoint, drop_all, seed_data.
- Hata: `RuntimeError` — sessizce geç değil.
- Test: guard fixture'da devre dışı bırakılabilir.

---

## Guidelines

```python
import os
from functools import wraps
from typing import Callable

def dev_only(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        env = os.getenv("ENV", "development").lower()
        if env == "production":
            raise RuntimeError(
                f"{fn.__name__} sadece geliştirme ortamında çalışır. "
                f"Mevcut ENV={env}"
            )
        return fn(*args, **kwargs)
    return wrapper

def require_env(allowed: list[str]):
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current = os.getenv("ENV", "development").lower()
            if current not in [e.lower() for e in allowed]:
                raise RuntimeError(
                    f"{fn.__name__} yalnızca şu ortamlarda çalışır: {allowed}. "
                    f"Mevcut: {current}"
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@dev_only
def seed_database():
    pass

@require_env(["development", "staging"])
def run_migration_preview():
    pass

def is_production() -> bool:
    return os.getenv("ENV", "development").lower() == "production"

def is_development() -> bool:
    return os.getenv("ENV", "development").lower() == "development"
```

---

## References

- `environment-detection-skill/SKILL.md` — ortam tespiti
- `settings-validation-skill/SKILL.md` — ayar doğrulama
- `env-file-setup-skill/SKILL.md` — ortam dosyası
