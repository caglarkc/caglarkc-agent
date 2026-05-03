---
name: env-file-setup
description: Coder AI için — .env dosyasını ve .env.example şablonunu oluşturmak; ortam değişkenlerini güvenli şekilde yönetmek.
---

## Purpose

Gizli anahtarlar kaynak koduna girmez — `.env` dosyasında tutulur.
`.env.example` yeni geliştirici için şablon sağlar.
`.gitignore`'a `.env` eklenmezse gizli bilgi repo'ya gider.

---

## When to Apply

- Yeni proje kurulumunda
- Yeni environment variable eklendiğinde
- `Settings` sınıfına yeni alan eklenirken

---

## Rules

- `.env`: gerçek değerler — `.gitignore`'da olmalı.
- `.env.example`: placeholder değerler — repo'ya girer.
- Gizli anahtar: `your_key_here` gibi açık placeholder.
- Yorumlar: her değişkenin amacını açıklar.
- Production'da `.env` yerine gerçek env var kullanılır.

---

## Guidelines

`.env.example` şablonu:
```bash
# LLM Providers
GEMINI_API_KEY=your_gemini_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=codellama:13b
OPENROUTER_API_KEY=your_openrouter_key_here

# Telegram (opsiyonel)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
DB_PATH=caglarkc_agent.db
CHECKPOINT_DB_PATH=graph_checkpoint.db

# Uygulama
MAX_CONCURRENT_WORKERS=3
MAX_RETRIES=3
LOG_LEVEL=INFO
```

`.gitignore` kontrolü:
```python
# setup.py veya proje başlatma scriptinde
def check_gitignore() -> None:
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        gitignore.write_text(".env\n__pycache__/\n*.pyc\n")
        return
    
    content = gitignore.read_text()
    if ".env" not in content:
        with gitignore.open("a") as f:
            f.write("\n.env\n")
        logger.warning(".env .gitignore'a eklendi")
```

pydantic-settings ile yükleme:
```python
class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Ortam değişkeni .env'i override eder
        env_nested_delimiter = "__"
```

---

## References

- `settings-validation-skill/SKILL.md` — settings doğrulama
- `constant-and-config-extraction-skill/SKILL.md` — sabitler
- `api-key-masking-skill/SKILL.md` — anahtar maskeleme
