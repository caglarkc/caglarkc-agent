---
name: integration-requirement-analysis
description: Planner AI için — sistemin dış servisler, API'lar ve diğer bileşenlerle nasıl entegre olacağını analiz etmek; entegrasyon noktalarını ve bağımlılıkları belirlemek.
---

## Purpose

Dış bağımlılıkları ve entegrasyon noktalarını sprint planına dahil eder.
Hangi servisin ne zaman ayakta olması gerektiğini belirler.
Entegrasyon başarısızlık senaryolarını planlar.

---

## When to Apply

- Yeni bir dış servis (API, bot, DB) ekleneceğinde
- Mevcut entegrasyona değişiklik yapılacağında
- Worker'ın dış kaynaktan veri çekeceği görevlerde
- Provider fallback zinciri tasarlanırken

---

## Rules

- Her dış servis için: URL, kimlik doğrulama, timeout, fallback tanımlanmalı.
- Ollama entegrasyonu: `OLLAMA_BASE_URL` env var üzerinden, health check zorunlu.
- Telegram entegrasyonu: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` zorunlu.
- OpenRouter: primary + secondary key ayrı tutulur, her ikisi de opsiyonel.
- Gemini: `GEMINI_API_KEY` zorunlu, model `GEMINI_MODEL` env var.
- Tüm entegrasyon noktaları `src/config/settings.py`'de Pydantic field olarak tanımlanır.

---

## Guidelines

Entegrasyon analiz formatı:
```
SERVİS: <ad>
URL: <endpoint>
AUTH: <api key / token / none>
ENV VAR: <settings.py'deki alan adı>
TIMEOUT: <ms>
FALLBACK: <başarısız olursa ne yapılır>
HEALTH CHECK: <nasıl kontrol edilir>
SPRİNT ETKİSİ: <hangi göreve bağımlı>
```

Mevcut entegrasyonlar (referans):
- Gemini: `GEMINI_API_KEY`, model `gemini-2.5-flash`, fallback: heuristic planner
- Ollama: `http://127.0.0.1:11434`, model `qwen2.5-coder`, fallback: OpenRouter
- OpenRouter Primary: `OPENROUTER_API_KEY_PRIMARY`, fallback: secondary
- OpenRouter Secondary: `OPENROUTER_API_KEY_SECONDARY`, fallback: stub
- Telegram: `TELEGRAM_BOT_TOKEN`, opsiyonel (disabled olabilir)
- SQLite: `SQLITE_DB_PATH`, no fallback (critical)

---

## Examples

```
Talep: "Slack bildirimi ekle"

Entegrasyon Analizi:
SERVİS: Slack Webhook
URL: https://hooks.slack.com/services/...
AUTH: webhook URL (secret)
ENV VAR: SLACK_WEBHOOK_URL (yeni eklenecek)
TIMEOUT: 5000ms
FALLBACK: log warn, bildirim atlanır
HEALTH CHECK: startup'ta ping
SPRİNT ETKİSİ: src/interfaces/ yeni modül, event bus subscription
```

---

## References

- `technical-feasibility-check-skill/SKILL.md` — uygulanabilirlik
- `project-architecture-skill/SKILL.md` — mevcut entegrasyon yapısı
- `non-functional-requirement-extraction-skill/SKILL.md` — güvenilirlik gereksinimleri
