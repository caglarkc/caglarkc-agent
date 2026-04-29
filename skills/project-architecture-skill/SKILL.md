---
name: project-architecture
description: AI Development Team Orchestrator projesinin klasör yapısı, mimari kuralları, dosya sınırları, naming convention ve state şeması. Her kodlama görevinde ve review sürecinde referans alınır. Mimari kararlar bu skill'e göre verilir.
---

## Proje Özeti

**AI Development Team Orchestrator** — Gemini yönetici, 3 worker AI (Ollama Qwen2.5 + 2x OpenRouter) ile gerçek yazılım projeleri geliştiren, Telegram ve CLI üzerinden yönetilen, 7/24 çalışan sistem.

---

## Klasör Yapısı

```
ai-orchestrator/
├── src/
│   ├── core/                    # Sistem çekirdeği
│   │   ├── event_bus.py         # Telegram-CLI senkronizasyonu
│   │   ├── state_manager.py     # Görev/sprint durumu
│   │   ├── project_manager.py   # Proje dosya yönetimi
│   │   ├── graph_manager.py     # Graph resume, crash recovery, EventBus → LangGraph köprüsü
│   │   └── context_builder.py   # SQLite'tan özet çekip Gemini prompt'una inject
│   │
│   ├── graph/                   # LangGraph katmanı
│   │   ├── state.py             # OrchestratorState TypedDict
│   │   ├── graph.py             # Grafik tanımı ve compile
│   │   ├── edges.py             # Koşullu edge fonksiyonları
│   │   └── nodes/               # Her node ayrı dosya
│   │       ├── planner.py       # Gemini planner node
│   │       ├── reviewer.py      # Gemini reviewer node
│   │       ├── worker.py        # Generic worker node (A/B/C)
│   │       ├── dispatcher.py    # Queue yönetimi, heartbeat
│   │       └── validator.py     # Kod syntax/import kontrolü
│   │
│   ├── interfaces/              # Kullanıcı arayüzleri
│   │   ├── telegram/
│   │   │   ├── bot.py           # Bot tanımı ve handler'lar
│   │   │   ├── handlers.py      # Komut handler'ları
│   │   │   └── notifier.py      # Bildirim gönderici
│   │   └── cli/
│   │       ├── app.py           # Textual app
│   │       ├── panels.py        # UI panelleri
│   │       └── notifier.py      # CLI bildirim
│   │
│   ├── config/                  # Konfigürasyon
│   │   ├── settings.py          # pydantic-settings
│   │   ├── prompts.py           # Gemini sistem promptları
│   │   └── logging_config.py    # RotatingFileHandler + RichHandler kurulumu
│   │
│   └── storage/                 # Kalıcı depolama
│       ├── models.py            # SQLite modelleri
│       └── repository.py        # DB işlemleri
│
├── projects/                    # Kullanıcı projelerinin çıktısı
│   └── <proje-adı>/
│       ├── .meta/               # Plan, sprint geçmişi
│       │   ├── plan.json
│       │   └── sprints/
│       └── <kaynak kodlar>
│
├── logs/                        # Sistem logları
├── .env                         # API key'ler
├── pyproject.toml               # Bağımlılıklar
├── main.py                      # Entry point
└── ai-orchestrator.service      # systemd service dosyası
```

---

## Katman Kuralları

### `src/core/` — Çekirdek
- Singleton pattern zorunlu
- Hiçbir dış bağımlılık (LangGraph, Telegram) import etmez
- Sadece standart kütüphane + pydantic + aiosqlite kullanır
- Tüm state buradan yönetilir, başka yerden state yazılmaz
- `graph_manager.py`: GraphManager — LangGraph thread resume/recover, EventBus `plan.approved/rejected` dinler ve `graph.ainvoke(Command(resume=...))` ile graph'ı devam ettirir. Tüm sistemin merkezi köprüsü
- `context_builder.py`: ContextBuilder — her Gemini çağrısı öncesi SQLite'tan özet üretir, max 2000 token, öncelik hiyerarşili (mimari kararlar → son sprintler → eski detaylar)

### `src/graph/` — LangGraph Katmanı
- Sadece LangGraph ve LangChain provider import'ları
- `core/` modüllerini import edebilir
- `interfaces/` import edemez
- Worker node'ları sadece `projects/<proje>/` altına yazar
- Her node fonksiyon olarak tanımlanır, state alır state döner
- Tüm node fonksiyonları async olmalı

### `src/interfaces/` — Arayüzler
- `core/event_bus.py` üzerinden iletişim kurar
- Birbirini import etmez (telegram ↔ cli izole)
- `crew/` katmanını direkt çağırmaz
- Sadece EventBus'a event gönderir / dinler

### `src/config/` — Config
- `.env` dışından değer okunmaz
- Hardcode string/key yasak
- `settings.py` tek config kaynağı

### `src/storage/` — Depolama
- Tüm DB işlemleri buradan
- `crew/` ve `interfaces/` direkt DB'ye erişmez
- Repository pattern zorunlu

---

## Naming Convention

| Tür | Format | Örnek |
|---|---|---|
| Dosya | snake_case | `state_manager.py` |
| Class | PascalCase | `StateManager` |
| Fonksiyon | snake_case | `get_active_sprint` |
| Async fonksiyon | snake_case + async | `async def send_message` |
| Sabit | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| Event | snake_case string | `"sprint.started"` |
| Config key | UPPER_SNAKE .env'de | `GEMINI_API_KEY` |

---

## State Şeması

### Proje State (`projects/<ad>/.meta/plan.json`)
```json
{
  "project_id": "uuid",
  "name": "proje adı",
  "description": "açıklama",
  "status": "planning|active|paused|completed",
  "created_at": "iso8601",
  "sprints": [],
  "current_sprint": null
}
```

### LangGraph State (`OrchestratorState` TypedDict)
```python
{
  # Proje kimliği
  "project_id": str,
  "project_name": str,
  "task_description": str,

  # Dosya yönetimi
  "file_registry": dict,       # {filename: "planned"|"reserved"|"in_progress"|"done"|"failed"}
  "dependencies": dict,        # {filename: [depends_on_files]}
  "worker_queue": list,        # [{"file": ..., "description": ..., "worker_hint": ...}]

  # Worker durumu
  "worker_status": dict,       # {"worker_a": "idle"|"working"|"done"|"error"}
  "worker_outputs": dict,      # {"worker_a": ["file1", "file2"]}
  "worker_failure_log": dict,  # {"worker_a": ["görev tipi 1", "görev tipi 2"]}

  # Sprint yönetimi
  "current_sprint": int,
  "sprint_type": str,          # "contract" | "feature"
  "sprint_status": str,        # "planning"|"active"|"review"|"completed"|"failed"
  "review_cycles": int,

  # Onay
  "awaiting_approval": bool,
  "approval_type": str,        # "plan" | "sprint_start" | "scope_change"

  # Kapsam değişikliği
  "scope_changed": bool,       # True olunca edge akışı planner_node'a döner, DAG yeniden hesaplanır

  # Context
  "context_summary": str,

  # Hata ve bildirim
  "errors": list,
  "messages": list
}
```

### SQLite Modelleri (`src/storage/models.py`)

Temel tablolar:
- `Project` — proje bilgisi ve durumu
- `Sprint` — sprint geçmişi, review döngüsü, dosya listesi
- `Decision` — alınan mimari kararlar (ContextBuilder Tier 1)
- `WorkerFailureLog` — worker_id, task_type, error_msg, timestamp. ContextBuilder bu tablodan başarısız görev tiplerini Gemini'ye inject eder
- `FileRecord` — hangi dosyanın hangi sprint'te kim tarafından yazıldığı

### Sprint Geçmişi (SQLite + `.meta/`)
```json
{
  "sprint_id": "uuid",
  "number": 1,
  "type": "contract|feature",
  "status": "completed|failed",
  "files_written": ["path1", "path2"],
  "review_cycles": 2,
  "decisions": ["karar 1", "karar 2"],
  "revision_notes": ["revizyon 1"],
  "started_at": "iso8601",
  "completed_at": "iso8601"
}
```

### Context Inject Şeması
`ContextBuilder` her Gemini çağrısından önce şu veriyi SQLite'tan çekip string'e dönüştürür:
```
Aktif Proje: <ad> | Sprint: <numara> | Durum: <status>
Tamamlanan Sprintler: <özet liste>
Yazılan Dosyalar: <son sprint dosyaları>
Mimari Kararlar: <kayıtlı kararlar, max 5 son kayıt>
Revizyon Geçmişi: <tekrarlayan hatalar, varsa>
```
Bu string `kickoff_async(inputs={"context": ...})` ile inject edilir.
Aynı string `.meta/context.md`'ye yazılır (sadece debug/insan okur, Gemini okumak zorunda değil).

### EventBus Events
```
task.received          # Kullanıcıdan görev geldi
plan.generated         # Gemini plan üretti
plan.approval_needed   # Kullanıcı onayı bekleniyor (LangGraph interrupt)
plan.approved          # Onaylandı → graph.resume()
plan.rejected          # Reddedildi → graph iptal
sprint.started         # Sprint başladı
sprint.worker_done     # Worker bir dosyayı bitirdi
sprint.review_started  # Gemini review başladı
sprint.revision_needed # Revizyon gerekiyor
sprint.completed       # Sprint tamamlandı
project.completed      # Proje tamamlandı
system.heartbeat       # Dispatcher 60s'de bir emit eder
system.stalled         # 10 dakika aktivite yok
system.recovered       # Crash sonrası graph resume edildi
error.occurred         # Hata oluştu
worker.retry           # Bir dosya başka worker'a yeniden atandı
worker.failed          # 3 retry sonunda hâlâ başarısız
```

---

## Bağımlılıklar

```toml
[project]
name = "ai-orchestrator"
requires-python = ">=3.11"

[dependencies]
langgraph = ">=0.2.0"
langchain-google-genai = ">=2.0.0"
langchain-community = ">=0.3.0"
langchain-openai = ">=0.2.0"
python-telegram-bot = ">=21.0"
textual = ">=0.80.0"
rich = ">=13.0"
pydantic-settings = ">=2.0"
httpx = ">=0.27.0"
aiosqlite = ">=0.20.0"
```

---

## Ortam Değişkenleri (.env)

```
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

---

## Worker Dosya Sınırları

Worker node'ları sadece `file_registry`'de kendilerine "reserved" olarak atanmış dosyalara yazar:
- Dispatcher bir dosyayı worker'a atamadan önce `file_registry`'de "reserved" işaretler
- Worker tamamladığında "done" olarak günceller
- Başka worker "reserved" veya "done" dosyaya yazamaz (dispatcher kontrolü)

Okuma serbest — tüm worker'lar `projects/<proje>/` altını okuyabilir.
Yazma kısıtlı — sadece kendi reserved dosyasına yazar.

---

## Mimari Prensipler

1. **EventBus merkezi** — tüm bileşenler arası iletişim EventBus üzerinden
2. **Interface izolasyonu** — Telegram ve CLI birbirini bilmez
3. **Graph bağımsızlığı** — interface'ler LangGraph'ı direkt çağırmaz, EventBus üzerinden iletişim kurar
4. **LangGraph state tek kaynak** — tüm orkestrasyon state'i `OrchestratorState`'te, başka yerden state yazılmaz
5. **Async everywhere** — tüm I/O async, blocking call yasak
6. **Config merkezi** — settings.py tek config kaynağı
7. **Worker sınırları** — her worker yalnızca `file_registry`'de rezerve edilmiş dosyasına yazar
8. **Context inject** — Gemini her çağrıda ContextBuilder özeti alır (öncelik hiyerarşili, max 2000 token)
9. **SQLite ground truth** — LangGraph SqliteSaver + repository, `.meta/context.md` sadece türev
10. **DAG first** — sprint başlamadan bağımlılık grafiği hazır, dispatcher DAG'a göre sıra verir
11. **Contract sprint önce** — her proje ilk sprint'te API contract, shared types, klasör yapısı üretir