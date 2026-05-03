---
name: env-var-validation
description: Coder AI için — daemon başlarken tüm zorunlu environment variable'ların varlığını ve geçerliliğini kontrol etmek; eksik config ile sessizce çalışmayı önlemek.
---

## Purpose

Daemon'ın eksik API key veya yanlış config ile başlamasını erken önler.
"Neden çalışmıyor?" sorusunu Pydantic validation hatasıyla açıkça yanıtlar.
Zorunlu ve opsiyonel env var'ları ayrıştırır.

---

## When to Apply

- `src/config/settings.py`'e yeni alan eklenirken
- Daemon startup kodu yazılırken
- Preflight check scripti oluşturulurken

---

## Rules

- Zorunlu env var: default değer olmadan `Settings` field olarak tanımlanır.
- Eksik zorunlu alan → `ValidationError` fırlatır — daemon başlamaz.
- Opsiyonel alan: `field | None = None` veya default değer ile.
- Startup'ta zorunlu bağlantılar test edilir (Gemini, Ollama health check).
- `.env.example` her zorunlu alanı içermeli.

---

## Guidelines

Zorunlu vs opsiyonel field tanımı:
```python
class Settings(BaseSettings):
    # Zorunlu — default yok, eksikse ValidationError
    GEMINI_API_KEY: SecretStr
    
    # Opsiyonel — None default
    OPENROUTER_API_KEY_PRIMARY: SecretStr | None = None
    TELEGRAM_BOT_TOKEN: SecretStr | None = None
    
    # Opsiyonel — anlamlı default
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    LOG_LEVEL: str = "INFO"
    STALL_TIMEOUT_SECONDS: int = 600
```

Startup validation:
```python
async def preflight_check():
    settings = get_settings()  # ValidationError burada fırlar
    
    # Gemini bağlantı testi
    try:
        model = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key.get_secret_value()
        )
        await model.ainvoke([HumanMessage(content="ping")])
        logger.info("Gemini bağlantısı OK")
    except Exception as e:
        logger.critical(f"Gemini bağlantısı başarısız: {e}")
        raise SystemExit(1)
    
    # Ollama health check (opsiyonel)
    if settings.ollama_base_url:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
            logger.info("Ollama bağlantısı OK")
        except Exception:
            logger.warning("Ollama erişilemiyor, OpenRouter fallback kullanılacak")
```

`.env.example` şablonu:
```bash
# Zorunlu
GEMINI_API_KEY=your_gemini_api_key_here

# Opsiyonel
OPENROUTER_API_KEY_PRIMARY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
OLLAMA_BASE_URL=http://127.0.0.1:11434
LOG_LEVEL=INFO
```

---

## References

- `pydantic-settings-definition-skill/SKILL.md` — settings tanımı
- `api-key-masking-skill/SKILL.md` — güvenli key yönetimi
- `technical-feasibility-check-skill/SKILL.md` — bağımlılık kontrolü
