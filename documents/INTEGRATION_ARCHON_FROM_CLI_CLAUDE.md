# ARCHON ← cli-claude referans entegrasyonu

Bu doküman, **ARCHON** (LangGraph tabanlı orkestratör) projesine `cli-claude` kod tabanından **hangi davranışların** taşınabileceğini ve nereye oturacağını özetler. Amaç kod kopyalamak değil; **desen ve dosya referansları** ile hızlı entegrasyon planı vermektir.

---

## Referans: cli-claude kaynak yolu

Bu bilgisayarda monorepo kökü üzerinden tam yol:

**`/home/caglarkc/Desktop/Github/sentinel-coming/agentic/cli-claude/`**

- Masaüstü → `Github` → `sentinel-coming` → `agentic` → `cli-claude` ile aynı konuma gelinir.
- Kaynak ağacı: `.../agentic/cli-claude/src/`

İlgili alt dizin örnekleri:

| Konu | Göreli yol (`src/` altından) |
|------|-------------------------------|
| Auto-dream | `services/autoDream/` |
| Bellek çıkarma (fork) | `services/extractMemories/` |
| Fork + izolasyon | `utils/forkedAgent.ts` |
| Tur sonu tetik | `query/stopHooks.ts` |
| Post-sampling hook | `utils/hooks/postSamplingHooks.ts`, `services/MagicDocs/magicDocs.ts`, `services/SessionMemory/sessionMemory.ts`, `utils/hooks/skillImprovement.ts` |
| Kompakt / bağlam | `services/compact/` |
| Uzakta “geri geldin” özeti | `services/awaySummary.ts` |
| Arka plan başlatma | `utils/backgroundHousekeeping.ts` |

---

## Mimari eşleme (ARCHON bileşeni → cli-claude deseni)

| ARCHON | Önerilen cli-claude deseni | Not |
|--------|---------------------------|-----|
| LangGraph node tamamlandıktan sonra | `handleStopHooks` içindeki `void execute…` (fire-and-forget) | Bloklamayan arka plan işleri |
| `EventBus` / TUI güncellemesi | `onMessage` + görev state (ör. `tasks/DreamTask/`) | Sadece UI ihtiyacı varsa sadeleştir |
| `context_builder` / Planner girdisi | Session memory + consolidation prompt | Özet diske, Planner’a kısa prefix |
| `projects/<id>/.meta/` | `getAutoMemPath()` + `.consolidate-lock` mantığı | Kilit = son birleştirme zamanı + PID |
| Worker dosya yazımı | `createAutoMemCanUseTool` (yalnızca bellek kökü + read-only bash) | Güvenlik sınırı |
| 360× `SKILL.md` bakımı | `skillImprovement.ts` + GrowthBook eşiği | Periyodik “skill öneri” job’u |
| Telegram / daemon “geri döndüm” | `awaySummary.ts` + küçük model | Kısa recap mesajı |

---

## Öncelikli entegrasyon maddeleri

### P0 — Dreaming + ham hafıza hattı

1. **Konsolidasyon (dream):** Zaman + oturum sayısı eşiği + dosya kilidi; ardından **ikinci bir LLM çağrısı** (ana thread’i bloklamadan) ile proje hafızası dosyalarını birleştirme.  
   - Referans: `services/autoDream/autoDream.ts`, `consolidationPrompt.ts`, `consolidationLock.ts`

2. **Ham çıktı (extract benzeri):** Her sprint veya her N turda “kalıcı not” üretimi; dream bunları birleştirir.  
   - Referans: `services/extractMemories/extractMemories.ts` (`createAutoMemCanUseTool` politikası dahil)

### P1 — Hook çatısı ve uzun bağlam

3. **Post-node / post-turn hook listesi:** Sırayla çalışan, hata toleranslı hook’lar.  
   - Referans: `utils/hooks/postSamplingHooks.ts`

4. **Uzun state / transcript özet stratejisi:** Token eşiği aşılınca özet dosyası + indeks.  
   - Referans: `services/compact/`, `services/SessionMemory/sessionMemory.ts`

### P2 — UX ve bakım

5. **Away summary:** Daemon veya Telegram için kısa “nerede kaldık”.  
   - Referans: `services/awaySummary.ts`

6. **Skill improvement:** Proje skill’lerine yönelik periyodik öneri (ARCHON’da 360 skill için yüksek ROI).  
   - Referans: `utils/hooks/skillImprovement.ts`

7. **Arka plan throttle:** Yoğun kullanımda ağır işleri erteleme.  
   - Referans: `utils/backgroundHousekeeping.ts`

---

## Python / LangGraph uygulama notları

- **Async:** cli-claude çoğunlukla promise/async; ARCHON `asyncio` — her “fork” için `asyncio.create_task` + iptal (`AbortController` → `asyncio.Event` / `Task.cancel()`).
- **Kilit:** Tek yazar için `fcntl` / `filelock` veya SQLite advisory lock; cli-claude `.consolidate-lock` + `utimes` ile geri sarma.
- **İzolasyon:** Alt çağrıda ayrı checkpoint veya en azından ayrı mesaj listesi; ana Planner mesaj listesini şişirmeyin (`skipTranscript` fikri).

---

## Bilerek taşımayın (ARCHON için)

- KAIROS özel araçları (cron, push, sleep, bridge) — ürün yüzeyi farklı.
- GrowthBook — başlangıçta `env` + kendi config’iniz yeterli.
- Coordinator / swarm — zaten Dispatcher + dosya rezervasyonunuz var; çift orkestrasyon riski.

---

## Doğrulama checklist’i

- [ ] Konsolidasyon yalnızca **onaylı sprint** veya **kapalı sprint** sonrası mı çalışacak? (ARCHON onay modeliyle hizalayın.)
- [ ] Hafıza kökü: repo içi mi (`projects/...`), global mi (`DATA_DIR/...`)?
- [ ] Planner’a giden özet **PII / secret** içeriyor mu? (Redaksiyon veya hafıza dışı bırakma kuralı.)
- [ ] Maliyet: dream + extract için aylık token üst sınırı ve kill switch.

---

## Lisans ve türetilmiş çalışma

`agentic/cli-claude` Anthropic kaynaklı ayrı bir ürün ağacıdır; ARCHON repo’suna kod alırken **lisans ve atıf** kurallarına uyun; mümkünse **davranışı yeniden yazıp** bu dokümandaki dosya yollarını referans olarak kullanın.

---

*Son güncelleme: 2026 — referans yolu bu makinedeki monorepo ile sabitlendi.*
