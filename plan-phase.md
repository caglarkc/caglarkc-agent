# AI Development Team Orchestrator — Faz Planı

> Ana plan için: `main-plan.md`  
> Her faz tamamlanınca durum güncellenir: ⬜ Bekliyor → 🔄 Aktif → ✅ Tamamlandı

---

## Faz 1 — Altyapı ve Bağlantılar

**Durum**: ✅ Tamamlandı  
**Amaç**: Tüm AI sağlayıcıları bağla, LangGraph kurulumunu doğrula, core iskelet ve storage schema'sını hazırla.  
**Skill**: `langgraph-patterns`, `project-architecture`

### Görevler

- [ ] Proje klasör yapısını oluştur (`project-architecture` skill'e göre)
- [ ] `pyproject.toml` ve `.env` şablonunu oluştur
- [ ] `src/config/settings.py` — pydantic-settings ile tüm env değişkenleri
- [ ] `src/config/logging_config.py` — RotatingFileHandler + RichHandler kurulumu
- [ ] Core iskelet dosyaları oluştur:
  - `src/core/event_bus.py` — Singleton EventBus, subscribe/emit
  - `src/core/state_manager.py` — Async-safe Singleton, Lock ile state yönetimi
  - `src/core/project_manager.py` — Proje dosya yönetimi iskelet
  - `src/core/context_builder.py` — ContextBuilder iskelet (Gemini prompt inject için, öncelik hiyerarşili)
- [ ] Storage katmanı oluştur:
  - `src/storage/models.py` — SQLite modelleri (Project, Sprint, FileRecord, Decision, WorkerFailure)
  - `src/storage/repository.py` — Repository pattern, tüm DB işlemleri
- [ ] LangGraph kurulumu ve Gemini bağlantı testi (`langchain-google-genai`)
- [ ] Ollama Qwen2.5 Coder bağlantı testi (`langchain-community`)
- [ ] OpenRouter 2x bağlantı testi (`langchain-openai`, her key ayrı ayrı)
- [ ] LangGraph SqliteSaver checkpointer bağlantı testi
- [ ] Basit 3-node LangGraph grafiği çalıştır (planner → worker → reviewer) — entegrasyon kanıtı

### Başarı Kriteri

Gemini, Ollama ve her iki OpenRouter bağlantısı çalışıyor. LangGraph SqliteSaver state kaydediyor ve resume edebiliyor. Core iskelet import hatası vermeden çalışıyor. SQLite schema oluşturuluyor.

---

## Faz 1.5 — Orchestration Contract ve Çalışma Sözleşmeleri

**Durum**: ✅ Tamamlandı  
**Amaç**: Graph, storage, interface ve worker davranışları için tek bir sözleşme katmanı tanımlamak.  
**Skill**: `project-architecture`, `langgraph-patterns`, `python-async-patterns`  
**Bağımlılık**: Faz 1 tamamlanmış olmalı

### Görevler

- [ ] `docs/contracts/orchestration_contract.md` oluştur:
  - Kimlik modeli: `project_id`, `thread_id`, `sprint_id`, `task_id`, `approval_id` ilişki şeması
  - Event payload şeması (zorunlu alanlar: `event_id`, `project_id`, `thread_id`, `timestamp`, `version`)
  - `interrupt/resume/reject/cancel` sözleşmesi ve payload örnekleri
- [ ] Retry/Error taxonomy tanımla:
  - Retryable: timeout, 429, geçici provider hataları
  - Non-retryable: invalid config, şema ihlali, policy ihlali
  - Backoff: exponential + jitter, max 3 retry
- [ ] Approval güvenlik modeli:
  - `approval_id` ve `idempotency_key` zorunlu
  - stale approval koruması (yalnızca aktif sprint + aktif approval kabul edilir)
  - onay timeout (varsayılan 15 dk) ve timeout sonrası durum geçişi
- [ ] State update protokolü yaz:
  - `file_registry`, `worker_queue`, `worker_status` güncellemeleri atomik
  - lock kapsamı: proje bazlı lock
  - SQLite transaction sınırları ve rollback şartları
- [ ] Test sözleşmesi:
  - contract lint/check adımı (`scripts/check_contracts.py` veya eşdeğeri)
  - örnek payload fixture dosyaları

### Başarı Kriteri

Tüm node ve interface akışları tek bir contract dokümanına bağlı. Rastgele `resume` veya eski onay mesajı ile state değişmiyor. Retry davranışı hatanın sınıfına göre deterministik çalışıyor.

---

## Faz 2 — LangGraph Core: State ve Graph Yapısı

**Durum**: ✅ Tamamlandı  
**Amaç**: Projenin ana state makinesini ve node/edge yapısını inşa et.  
**Skill**: `langgraph-patterns`, `python-async-patterns`  
**Bağımlılık**: Faz 1 + Faz 1.5 tamamlanmış olmalı

> **Not — Geçici Onay Mekanizması**: Bu fazda onay LangGraph `interrupt()` ile konsoldan alınır. CLI (Faz 5) ve Telegram (Faz 6) tamamlanınca EventBus üzerinden replace edilir.

### Görevler

- [ ] `src/graph/state.py` — `OrchestratorState` TypedDict tanımı:
  - `file_registry`: her dosyanın durumu (planned/assigned/in_progress/done/failed)
  - `dependencies`: dosya bağımlılık grafiği (DAG)
  - `worker_status`: her worker'ın durumu (idle/working/done/error)
  - `worker_queue`: atanmayı bekleyen iş birimleri
  - `worker_failure_log`: her worker'ın başarısız olduğu görev tipleri
  - `current_sprint`, `sprint_status`, `review_cycles`
  - `context_summary`, `awaiting_approval`, `approval_type`
- [ ] `src/graph/nodes/planner.py` — Gemini planner node:
  - Görevi alır, dosya listesi + bağımlılık grafiği üretir
  - Contract sprint mi, feature sprint mi karar verir
  - `context_summary` inject edilerek çağrılır
- [ ] `src/graph/nodes/reviewer.py` — Gemini reviewer node:
  - Tüm sprint çıktısını değerlendirir (ONAY / REVİZYON / FAIL)
  - Revizyon notlarını state'e yazar
  - Başarısız worker pattern'ını `worker_failure_log`'a ekler
- [ ] `src/graph/nodes/worker.py` — Generic worker node (A/B/C için aynı kod, LLM parametre):
  - Queue'dan iş alır, bağımlılıkları kontrol eder
  - Dosyaya yazar (pathlib, direkt)
  - State'e "done" işaretler, EventBus'a `sprint.worker_done` emit eder
- [ ] `src/graph/nodes/dispatcher.py` — Dispatcher node:
  - Queue'ya bak, bağımlılıkları kontrol et, idle worker'a iş ata
  - Heartbeat: 60 saniyede bir EventBus'a `system.heartbeat` emit eder
- [ ] `src/graph/nodes/validator.py` — Code validator node:
  - Python dosyaları için `py_compile` syntax kontrolü
  - Import varlığı kontrolü
  - Hata varsa state'e yaz, reviewer'a ilet
- [ ] `src/graph/edges.py` — Koşullu edge fonksiyonları:
  - `route_after_dispatch`: queue boşsa reviewer'a, doluysa worker node'larına
  - `route_after_review`: approved → next sprint veya END, revision → dispatcher, fail → kullanıcı bildirimi
  - `route_after_worker`: bağımlılıklar karşılandıysa dispatcher'a, değilse bekle
- [ ] `src/core/graph_manager.py` — GraphManager:
  - EventBus `plan.approved/rejected` olaylarını dinleyip `Command(resume=...)` köprüsü kurar
  - `approval_id`, `thread_id` ve `sprint_id` eşleşmesini doğrular
  - stale event'i güvenli şekilde reddeder, audit log yazar
- [ ] `src/graph/graph.py` — Grafik tanımı ve compile:
  - Node'ları bağla, edge'leri ekle
  - SqliteSaver checkpointer bağla
  - `interrupt_before=["await_approval"]` ile onay noktası
- [ ] Atomic state update garantisi:
  - Dispatcher atama + `file_registry=reserved` tek transaction
  - Worker completion + queue update tek transaction
  - Çakışma durumunda retry ve rollback
- [ ] Konsoldan görev ver → Gemini plan üretir → onay → dispatcher çalışır → workers dosya yazar → reviewer değerlendirir

### Başarı Kriteri

Konsoldan görev verildiğinde tüm graph akışı çalışıyor. Worker A bir dosya bitirince dispatcher otomatik yeni iş atıyor. Bağımlılık olan dosya, bağımlısı bitmeden başlamıyor. Graph state SQLite'a kaydediliyor, crash sonrası resume ediliyor. Yanlış/stale onay ile resume denemeleri reddediliyor.

---

## Faz 3 — Dinamik Worker Sistemi ve Bağımlılık Yönetimi

**Durum**: ✅ Tamamlandı  
**Amaç**: Dosya bazlı bağımlılık grafiği, dosya rezervasyonu ve contract sprint mekanizmasını tamamla.  
**Skill**: `langgraph-patterns`, `project-architecture`  
**Bağımlılık**: Faz 2 tamamlanmış olmalı

### Görevler

- [ ] **Contract Sprint**: Gemini proje tipini analiz edip ilk sprint'i contract sprint olarak üretir:
  - API şeması (`api_contract.json`)
  - Shared type tanımları (`shared_types.py` veya `types.ts`)
  - Klasör yapısı ve dosya listesi
  - Bu sprint bitmeden feature sprint başlamaz
- [ ] **Dosya Rezervasyon Sistemi**: `file_registry`'de bir dosya atandığında "reserved" işaretlenir, başka worker aynı dosyayı alamaz
- [ ] **DAG Bağımlılık Kontrolü**: Dispatcher, her iş birimini atamadan önce tüm bağımlılıklarının "done" olup olmadığını kontrol eder
- [ ] **Worker Failure Learning**: Reviewer revizyon yaparken hangi worker hangi tür görevde başarısız oldu `worker_failure_log`'a yazılır; ContextBuilder bu logu bir sonraki sprint'te Gemini'ye inject eder
- [ ] **Partial Failure Yönetimi**: Bir worker başarısız olursa:
  - Dosyası "failed" işaretlenir
  - Bağımlı dosyaların işi bloklanır
  - Görev başka bir worker'a yeniden atanır (retry logic)
  - 3 retry sonunda kullanıcı bildirilir
- [ ] **Scope Change Akışı**: Sprint aktifken kullanıcı yeni gereksinim eklerse:
  - Mevcut sprint duraklatılır
  - Gemini yeni gereksinimleri mevcut plana entegre eder
  - Etkilenen dosyalar yeniden planlanır
- [ ] `projects/<proje-adı>/` klasör yapısının sprint başında oluşturulması
- [ ] Sprint planının `.meta/plan.json`'a kaydedilmesi

### Başarı Kriteri

Farklı proje tiplerinde (full stack, backend only, CLI tool) Gemini doğru contract sprint üretiyor. Dosya çakışması olmuyor. Bağımlı dosyalar sırayla yazılıyor. Bir worker çöktüğünde görev başka worker'a geçiyor.

---

## Faz 4 — Review, Validasyon ve Context Yönetimi

**Durum**: 🔄 Aktif  
**Amaç**: Otomatik review döngüsünü, kod validasyonunu ve Gemini context inject sistemini tamamla.  
**Skill**: `langgraph-patterns`, `python-async-patterns`  
**Bağımlılık**: Faz 3 tamamlanmış olmalı

### Görevler

- [ ] **Reviewer node'unu tamamla**:
  - Kod kalitesi, eksik dosya, bağımlılık uyumu kontrolü
  - ONAY → sprint kapat, REVİZYON → sadece hatalı dosyaları tekrar kuyruğa at
  - Max 3 review döngüsü aşılırsa kullanıcıya bildir
- [ ] **Validator node'unu tamamla**:
  - Python: `py_compile` syntax + import varlık kontrolü
  - JSON: json.loads ile parse testi
  - Hata varsa reviewer'a iletmeden önce worker'a geri gönder
- [ ] **Deterministik policy kontrolleri**:
  - path traversal engelle (`..`, absolute path escape)
  - secrets redaction (log/prompt içinde token masking)
  - prompt güvenlik filtresi (yasaklı dosya/path override denemeleri)
- [ ] **ContextBuilder'ı tamamla** (öncelik hiyerarşili):
  - Tier 1 — asla atılmaz: mimari kararlar, contract dosyaları
  - Tier 2 — son 3 sprint özeti
  - Tier 3 — kısaltılabilir: eski sprint detayları, dosya listesi
  - Max 2000 token bütçesi, tier sırasına göre doldur
- [ ] **Decision logging**: Sprint review sonrası alınan mimari kararlar `repository.py` üzerinden SQLite'a yazılır
- [ ] **Sprint kapanış akışı**: `sprints/<sprint_id>.json` kaydı, EventBus `sprint.completed` emit
- [ ] **Heartbeat bildirimi**: Dispatcher 60 saniyede bir `system.heartbeat` emit eder; 10 dakika sessizlik → `system.stalled` event'i
- [ ] **Test stratejisi**:
  - Unit: validator/policy/retry kararları
  - Integration: planner→dispatcher→worker→reviewer döngüsü
  - E2E: crash sonrası resume + approval timeout + stale approval reddi

### Başarı Kriteri

Worker hatalı kod yazdığında validator yakalar, reviewer fark eder, revize ettirir. 3 döngü sonunda hâlâ hatalıysa kullanıcı uyarılır. ContextBuilder Tier 1 kararları hiç atmadan token bütçesine sığdırıyor. Test pipeline'ında unit+integration+e2e senaryoları yeşil.

Ölçülebilir hedefler:
- Review döngüsü p95 süresi ≤ 5 dk
- Validator false-negative oranı < %2
- Revizyon sonrası başarı oranı ≥ %85

---

## Faz 5 — CLI Arayüzü

**Durum**: ⬜ Bekliyor  
**Amaç**: PC başındayken görsel terminal arayüzü ile yönetim.  
**Skill**: `telegram-bot-patterns`, `python-async-patterns`  
**Bağımlılık**: Faz 4 tamamlanmış olmalı

### Görevler

- [ ] Textual app temel yapısı (`src/interfaces/cli/app.py`)
- [ ] Sol panel: aktif görevler ve sprint durumları (dosya bazında ilerleme)
- [ ] Sağ panel: canlı log akışı (RichLog)
- [ ] Alt panel: onay bekleyen kararlar (sarı highlight)
- [ ] Komut girişi: `/task`, `/status`, `/approve`, `/reject`, `/cancel`
- [ ] EventBus'a bağlanma — tüm graph event'lerini CLI'da göster
- [ ] LangGraph `interrupt()` onayını EventBus üzerinden karşıla (konsol onayını replace et)
- [ ] Heartbeat event'lerini göster — "son aktivite: X saniye önce"
- [ ] Onay güvenliği:
  - `/approve` yalnızca aktif `approval_id` ile çalışır
  - timeout olmuş onaylar UI'da pasif görünür
  - aynı onay için ikinci komut idempotent şekilde no-op olur

### Başarı Kriteri

Terminal açıkken tüm sistem aktivitesi görünüyor. `/task` ile görev verilebiliyor, onay ekranı çıkıyor, `/approve` ile LangGraph graph'ı resume ediyor. Timeout/stale onaylarda kullanıcı güvenli hata mesajı görüyor.

Ölçülebilir hedefler:
- Plan onayı p95 işlem süresi ≤ 2 sn (komut alımı → event publish)
- Duplicate approval komutlarında çift resume oranı = %0

---

## Faz 6 — Telegram Bot

**Durum**: ⬜ Bekliyor  
**Amaç**: 7/24 Telegram üzerinden görev verme ve takip.  
**Skill**: `telegram-bot-patterns`, `python-async-patterns`  
**Bağımlılık**: Faz 5 tamamlanmış olmalı (EventBus hazır)

### Görevler

- [ ] python-telegram-bot async yapısı (`src/interfaces/telegram/bot.py`)
- [ ] Komutlar: `/task`, `/status`, `/cancel`
- [ ] Plan onayı: inline keyboard (Onayla / Reddet / Revize Et)
- [ ] Sprint tamamlandı bildirimi (dosya sayısı, review döngüsü, süre)
- [ ] Hata bildirimi ve worker stall bildirimi
- [ ] Revizyon notu alma (metin mesajı olarak)
- [ ] LangGraph graph resume: Telegram onayı → EventBus → graph.resume()
- [ ] EventBus'a bağlanma — CLI ile senkron
- [ ] Güvenlik: sadece `TELEGRAM_CHAT_ID` yetkili
- [ ] Onay güvenliği:
  - callback data içinde `approval_id` + `idempotency_key`
  - timeout/stale callback reddi
  - hızlı tekrar tıklamada tek işlem garantisi

### Başarı Kriteri

Telegramdan `/task` ile görev veriliyor, plan inline keyboard ile onaylanıyor, sprint bildirimleri geliyor. Aynı anda CLI'da da görünüyor. Eski mesajdan gelen onay callback'leri state'i değiştiremiyor.

Ölçülebilir hedefler:
- Callback yanıt p95 süresi ≤ 3 sn
- Unauthorized chat denemelerinde başarı oranı = %0

---

## Faz 7 — 7/24 Daemon

**Durum**: ⬜ Bekliyor  
**Amaç**: Sistem PC açılınca otomatik başlasın, çökerse kendini kurtarsın.  
**Skill**: `daemon-ops`, `python-async-patterns`  
**Bağımlılık**: Faz 6 tamamlanmış olmalı

### Görevler

- [ ] `main.py` entry point — asyncio.gather ile tüm bileşenleri başlat
- [ ] Graceful shutdown (SIGTERM/SIGINT handler)
- [ ] Ollama health check — başlamadan önce bekle
- [ ] Crash recovery — başlangıçta pending LangGraph thread'lerini resume et (SqliteSaver üzerinden)
- [ ] `ai-orchestrator.service` systemd dosyası
- [ ] Log rotation ayarı (max 10MB, 5 dosya)
- [ ] Deployment checklist doğrulama
- [ ] Recovery playbook:
  - orphan `reserved` dosyaları tespit et ve güvenli reclaim et
  - replay-safe resume (aynı event iki kez işlenmez)
  - checkpoint/state checksum doğrulaması

### Başarı Kriteri

`sudo systemctl start ai-orchestrator` ile sistem başlıyor. PC yeniden başlatıldığında otomatik başlıyor. Crash sonrası 10 saniye bekleyip yeniden başlıyor ve kaldığı yerden devam ediyor. Orphan reservation temizliği sonrası dosya çakışması olmuyor.

Ölçülebilir hedefler:
- Crash sonrası restore süresi p95 ≤ 45 sn
- Replay-safe resume ihlali = 0

---

## Faz 8 — Proje Yönetimi

**Durum**: ⬜ Bekliyor  
**Amaç**: Proje geçmişi, istatistikler ve multi-proje desteği.  
**Skill**: `project-architecture`, `python-async-patterns`  
**Bağımlılık**: Faz 7 tamamlanmış olmalı

### Görevler

- [ ] `ProjectManager` sınıfını tamamla — proje listeleme, seçme, arşivleme
- [ ] `/projects` Telegram komutu — aktif projeleri listele
- [ ] Proje özeti: toplam sprint, toplam dosya, toplam süre, worker başarı oranları
- [ ] Sprint geçmişi görüntüleme (`/history <proje>`)
- [ ] Çoklu proje desteği — birden fazla LangGraph thread paralel çalışabilir
- [ ] Proje arşivleme — tamamlanan projeyi `.meta/archived` olarak işaretle
- [ ] Scheduler kapasite politikası:
  - fair queue (proje başına zaman dilimi)
  - proje başına concurrency limiti
  - provider quota/rate-limit aware dispatch + degrade mod

### Başarı Kriteri

Birden fazla proje yönetilebiliyor. Geçmiş projeler, sprint detayları ve worker performansı görüntülenebiliyor. Yoğunlukta tek proje tüm worker kaynaklarını kilitlemiyor.

Ölçülebilir hedefler:
- Fair queue ile starvation vakası = 0
- Proje başına queue bekleme süresi farkı p95 < 3x
- Provider fallback başarı oranı ≥ %90

---

## Bağımlılık Grafiği

```
Faz 1 → Faz 1.5 → Faz 2 → Faz 3 → Faz 4 → Faz 5 → Faz 6 → Faz 7 → Faz 8
```

Her faz bir öncekinin tamamlanmasını gerektirir.

---

## Operasyonel Gözlemlenebilirlik ve Limit Politikası

- [ ] Metrikler: `sprint_latency_seconds`, `retry_success_ratio`, `queue_stuck_seconds`, `provider_error_ratio`, `approval_latency_seconds`
- [ ] Her metrik için günlük rapor ve son 24 saat trend özeti
- [ ] OpenRouter quota/rate-limit aşımlarında otomatik degrade:
  - önce alternatif OpenRouter key/model
  - sonra Ollama fallback
  - son seçenek: sprint pause + kullanıcı bildirimi
- [ ] Alarm eşikleri:
  - `queue_stuck_seconds > 600`
  - `provider_error_ratio > 0.3` (5 dk pencere)
  - `approval_latency_seconds p95 > 120`

Bu bölüm Faz 4-8 teslimlerinde zorunlu kabul kriteri olarak uygulanır.

---

## Güncel Durum

**Aktif Faz**: Faz 4 — Review, Validasyon ve Context Yönetimi  
**Son Güncelleme**: Faz 3 tamamlandı, Faz 4 başlatıldı  
**Tamamlanan Faz**: Faz 1 — Altyapı ve Bağlantılar; Faz 1.5 — Orchestration Contract ve Çalışma Sözleşmeleri; Faz 2 — LangGraph Core: State ve Graph Yapısı; Faz 3 — Dinamik Worker Sistemi ve Bağımlılık Yönetimi
