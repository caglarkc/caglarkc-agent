# Codex için: Tam entegrasyon — önce ara, sonra bağla

Bu tek prompt yeni bir sohbette yapıştırılır. Repo yolu kullanıcıda farklı olabilir; kök klasör olarak `caglarkc-agent` varsayılır.

---

## PART A — SENDEN ÖNCELİKLİ İSTENEN DAVRANIŞ (BU SIRA ZORUNLU)

1. **Tam kod araması yap:** Repo genelinde `planner`, `task.received`, `GraphManager`, `worker`, `Gemini`, `ChatGoogle`, `ApprovalRequest`, `worker_queue`, `contract`, Telegram/CLI görev işleme dahil semantic + dosya bazlı ara. Amaç: **şu an plan ve görev zinciri kodda gerçekten nasıl bağlanmış**, net fotoğraf.
2. **Analizi yaz:** 10–25 satır; bulduğun kritik dosyalar (path).
3. **Eksik listesi çıkar:** Aşağıdaki **ÜRÜN TANIMINI** ile kıyası; ne var ne yok tek tek.
4. **Entegrasyon yap:** Kodu gerçekten değiştir; “öneride bulunmak” yerine `.py`/config/dokümantasyon.
5. **Ben (Claude) planlama yapmıyorum** — bu chat’te sadece bu prompt var; **planlama ve mimari karar sende** (sen Codex).

---

## PART B — KULLANICININ TAM OLARAK NE İSTEDİĞİ (ÜRÜN TANIMI — KAYNAK: `request.md` + DOĞRUDAN TALEP)

**Zorunlu okuma:** Repoda `request.md` dosyasını aç; aşağıdaki maddeler onunla çelişmeyecek şekilde uygulanır.

### B.1 Yönetici zekâsı (Gemini)

- Kullanıcı **planlama / gereksinim netleştirme / karşılıklı konuşma** modundayken **asıl beyin Gemini** olmalı (LangChain `ChatGoogleGenerativeAI` veya projede uyumlu adapter; `GEMINI_API_KEY` / `GEMINI_MODEL` zaten var).
- Bu modda amaç: kullanıcıyla **aynı Türkçe/İngilizce sohbeti** sürdürebilmek, soru-cevap ile kapsamı netleştirmek, **otomatik sabit dosya üçlüsünü kosulsuz seçmeyen** bir davranış.
- Varsayılan olarak **sessizce tüm codebase’i “contract sprint üç dosyası” diye yazdırma YOK.**

### B.2 Ne zaman kod / worker?

- Kod üretimi ve worker kuyruğuna düşecek iş **tek başına kullanıcıya “task attın bitsin”** diye çıkmaz; **`request.md`’teki ile uyumlu:** kod üretimi **açık niyet** ve uygun onboarding ile (örneğin aşama belirlendiğinde veya kullanıcı “haydi uygula / kod yaz / sprint başlat” benzeri bir onay verdikğinde).

### B.3 Onay ile planın işçilere gitmesi

- Kullanıcı **bir planı netleştirdiği ve sistemde bunu ONAYladığı anda**, o anda konuşulmuş/elde edilmiş plan **dispatcher + worker’a gidecek yapısal veri olarak** bağlanmalı (dosya listesi, bağımlılıklar, kısa açıklama; mevcut `DispatchAssignment` / `OrchestratorState` ile uyumlu veya gerekiyorsa mimari bunu doğru uzatır).
- “Site yap” dediğinde sonuç olarak **otomatik hep aynı üç backend dosya** çıkması kullanıcı niyetiyle uyumlu değildir; **isteğin türünü planlayanın ürettiği veya doğrulanan dosya kümesinin yansıması** beklenir (LLM çıktısı contract şemasında parse edilir; geçersizse reddedilir/tekrar istenir).

### B.4 Kanallar ve sözleşme

- **CLI ile Telegram:** Aynı orkestrasyon sözleşmesi (`EventEnvelope`, approval idempotent/stale korunur).

### B.5 Korunacak olanlar

- Mevcut: checkpoint, crash recovery, `ApprovalGuard`, event bus tabanlı UI senkronu, daemon girişi — **bilerek kırma**; yeni özellik bunların üzerine binsin.

---

## PART C — SANA BIRAKILAN TEKNİK KARARLAR

- Gemini sohbetini **LangGraph içinde yeni node** mı, **ayrı servis** mi, **planlama interrupt** mı — analizden sonra en az sürtünmeyle hangisi uygunsa onu seç.
- Plan çıktısını **JSON şeması** ile mi zorunlu kılarsın, **iki aşamalı** (özet → kullanıcı onayı → detay DAG) mı — sen karar ver.
- Eski deterministik contract sprint’i **tamamen sil** mi, **USE_LEGACY_PLANNER=1** ile devre dışı bırak** mı — sen karar ver; ama **varsayılan davranış** `request.md` ile uyumlu olmalı.

---

## PART D — KABUL (MİNİMUM)

- Kullanıcı senaryosu: “Site kur / API tasarla / şu modülü ekle” — **önce Gemini ile kısa bir plan diyaloğu** (en az bir tur model cevabı gerçekten Git API’den geliyor), ardından **onay** sonrası **o plana uygun** dosya kuyruğu ve worker üretimi (stub veya LLM mevcut worker katmanıyla).
- `request.md` non-goal’ları ihlal etme: **varsayılan tek komutla otomatik tam repo kod patlaması** olmasın.
- `main.py --cli` ve varsa Telegram ile **regresyon yok** (servis ayağa kalkar, eski approval güvenliği çalışır).

---

## PART E — DOKÜMANTASYON

- `docs/REAL_WORKER.md` veya yeni `docs/MANAGER_PLANNING.md` ile: nasıl mod geçilir, hangi env, örnek akış.
- `request.md` ile çelişen bir cümle yazma.

---

**Bitirince:** Kısa bir “ne değişti” listesi + hangi dosyalar + manuel test adımları (3–5 madde).
