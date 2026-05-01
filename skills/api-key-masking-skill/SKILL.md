---
name: api-key-masking
description: Coder AI için — API key, token ve şifre gibi hassas verilerin log'a, hata mesajına veya user output'a düşmemesini sağlamak.
---

## Purpose

Hassas verilerin accidental log exposure'ını önler.
Pydantic `SecretStr` tipiyle settings'te maskeleme sağlar.
Log mesajlarında key'in sadece ilk ve son karakterleri gösterilir.

---

## When to Apply

- API key içeren kod yazılırken
- Settings alanı log'a yazılırken
- HTTP istek header'ı oluşturulurken
- Exception mesajı oluşturulurken

---

## Rules

- API key'ler `SecretStr` tipiyle tanımlanır: otomatik maskelenir.
- `SecretStr` değerine `.get_secret_value()` ile erişilir (sadece çağrı anında).
- Log'da key gösteriminde: `key[:8] + "..." + key[-4:]` veya `key[:4] + "****"`.
- HTTP header'ında key: direkt kullanılır ama log'a yazılmaz.
- Exception mesajında key içeriyorsa maskelenir.
- `.env` dosyası `.gitignore`'da olmalı (kod meselesi değil ama hatırlatma).

---

## Guidelines

SecretStr kullanımı:
```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: SecretStr
    OPENROUTER_API_KEY_PRIMARY: SecretStr | None = None
    TELEGRAM_BOT_TOKEN: SecretStr | None = None

settings = get_settings()

# DOĞRU — .get_secret_value() sadece kullanım anında
api_key = settings.gemini_api_key.get_secret_value()

# YANLIŞ — string'e cast ederek maskelemeyi bypass etme
api_key = str(settings.gemini_api_key)  # "**" gösterir ama içeriği kaybetmez
```

Log'da maskeleme:
```python
def mask_api_key(key: str) -> str:
    if len(key) <= 12:
        return "****"
    return f"{key[:8]}...{key[-4:]}"

# Bağlantı durumu log'larken
logger.info(
    f"OpenRouter bağlantısı kuruldu",
    extra={"key_preview": mask_api_key(api_key)}
)

# Exception içinde key geçiyorsa
except httpx.HTTPStatusError as e:
    # Response body'de key olabilir — loglamadan önce sanitize et
    logger.error(f"HTTP {e.response.status_code}: {sanitize_response(str(e))}")
```

Header oluşturma:
```python
headers = {
    "Authorization": f"Bearer {settings.openrouter_api_key_primary.get_secret_value()}",
    # Log'a header dict'i yazma!
}
logger.debug("OpenRouter isteği gönderildi")  # header loglanmıyor
```

---

## References

- `pydantic-settings-definition-skill/SKILL.md` — SecretStr
- `logging-usage-review-skill/SKILL.md` — log güvenliği
- `env-var-validation-skill/SKILL.md` — env yönetimi
