# AI Development Team Orchestrator — Ana Proje Planı

> **Versiyon**: 1.0  
> **Durum**: Aktif Geliştirme  
> **Yönetici**: Claude (pm-mode)  
> **Kodlayan**: Codex (code-mode)

---

## Vizyon

Sana çalışan bir yazılım geliştirme ekibi. Sen **Tech Lead**'sin. Gemini **Project Manager**, 3 Worker AI **Developer**. Gerçek kod yazıyorlar, gerçek dosyalara, gerçek projeleri bitiriyorlar. Sen onaylıyor, yönlendiriyor, karar veriyorsun.

---

## Sistem Mimarisi

```
Sen (Telegram veya CLI)
        ↓
Gemini — Projeyi analiz eder, planlar, sunar, onay bekler
        ↓
Sprint başlar — Gemini rolleri dinamik atar
   Worker1 / Worker2 / Worker3
   (roller projeye göre değişir, sabit değil)
        ↓
Kod yazılır → dosyalara → Gemini review eder
        ↓
Hata varsa worker'a geri → düzeltilir
Tamam ise → sonraki sprint
        ↓
Proje biter → Sen bilgilendirilirsin
```

---

## Teknik Stack

| Bileşen | Teknoloji |
|---|---|
| Orchestration | LangGraph (state machine, DAG, conditional edges) |
| Manager AI | Gemini 2.5 Pro (planner + reviewer node) |
| Worker 1 | Ollama — Qwen2.5 Coder (lokal) |
| Worker 2 | OpenRouter — Free API Key 1 |
| Worker 3 | OpenRouter — Free API Key 2 |
| LLM Entegrasyon | langchain-google-genai, langchain-community, langchain-openai |
| CLI Arayüz | Rich + Textual |
| Telegram Bot | python-telegram-bot |
| State/Persistence | LangGraph SqliteSaver (checkpointer) |
| Daemon | systemd |
| Dosya Sistemi | Python pathlib (direkt yazma) |
| Config | pydantic-settings |
| Async | asyncio + httpx |

---

## Kritik Prensipler

1. **Onaysız başlamaz** — Gemini karar verir, sen onaylarsın. Hiçbir sprint onaysız başlamaz.
2. **Dinamik roller** — Worker rolleri sabit değil. Her proje/sprint başında Gemini atar.
3. **Otomatik hata döngüsü** — Worker hata yaparsa Gemini tekrar gönderir. Sen müdahale etmek zorunda değilsin.
4. **Arayüz senkronluğu** — Telegram ve CLI her zaman senkron. İkisinden de aynı aksiyonları yapabilirsin.
5. **Crash recovery** — Sistem çökerse SQLite persistence sayesinde kaldığı yerden devam eder.
6. **Sözleşme odaklı orkestrasyon** — ID/Event/Approval contract olmadan hiçbir kritik akış üretime alınmaz.
7. **Güvenli onay akışı** — Onaylar `approval_id` ve idempotency ile doğrulanır; stale onaylar state değiştiremez.
8. **Ölçülebilir kalite** — Faz kapanışları yalnızca ölçülebilir metriklerle yapılır (restore süresi, retry başarısı, fallback oranı).

---

## Faz Özeti

| Faz | Ad | Durum |
|---|---|---|
| 1 | Altyapı ve Bağlantılar | ✅ Tamamlandı |
| 1.5 | Orchestration Contract | ✅ Tamamlandı |
| 2 | Core Orchestration | ✅ Tamamlandı |
| 3 | Dinamik Worker Sistemi | ✅ Tamamlandı |
| 4 | Review ve Döngü Sistemi | ✅ Tamamlandı |
| 5 | CLI Arayüzü | 🔄 Aktif |
| 6 | Telegram Bot | ⬜ Bekliyor |
| 7 | 7/24 Daemon | ⬜ Bekliyor |
| 8 | Proje Yönetimi | ⬜ Bekliyor |

> Detaylı faz planı için: `PHASE_PLAN.md`

---

## Skill Referansları

| Skill | Amaç |
|---|---|
| `pm-mode` | Claude yönetici davranış kuralları |
| `code-mode` | Codex kodlama kuralları |
| `project-architecture` | Klasör yapısı, mimari, state şeması |
| `langgraph-patterns` | LangGraph state, node, edge, DAG, HITL |
| `python-async-patterns` | EventBus, daemon, async kurallar |
| `telegram-bot-patterns` | Bot yapısı, onay mekanizması, CLI |
| `daemon-ops` | systemd, log yönetimi, deployment |

---

## Mimari Özet

```
src/
├── core/          # EventBus, StateManager, ProjectManager, ContextBuilder
├── graph/         # LangGraph: state, nodes, edges, graph tanımı
├── interfaces/    # telegram/ ve cli/ — EventBus üzerinden bağlı
├── config/        # settings.py, prompts.py, logging_config.py
└── storage/       # SQLite modelleri ve repository

projects/          # Kullanıcı projelerinin çıktısı
logs/              # Sistem logları
```

> Tam mimari detaylar: `project-architecture` skill

---

## Ortam Değişkenleri

```env
GEMINI_API_KEY=
OPENROUTER_API_KEY_1=
OPENROUTER_API_KEY_2=
OPENROUTER_MODEL_1=
OPENROUTER_MODEL_2=
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
PROJECTS_DIR=./projects
LOG_LEVEL=INFO
```