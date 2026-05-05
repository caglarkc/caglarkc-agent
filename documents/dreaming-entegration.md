
# Auto-dream / bellek konsolidasyonu — entegrasyon notları (kaynak: cli-claude)

## 1. Kavramsal özet

**Amaç:** Ana ajanın konuşması bittikten sonra, **ayrı bir alt ajan çağrısı** ile proje **hafıza dizinindeki** Markdown (ve benzeri) dosyalarını okuyup birleştirmek, indeksi güncellemek, tekrar ve çelişkiyi azaltmak.

**Ne değildir:**

- Sürekli “idle loop” veya modelin kendi ağırlığını güncellemesi yok.
- Ana thread’in transcript’ine doğrudan yazılmıyor (`skipTranscript: true`); isteğe bağlı kısa bir **sistem** özeti eklenebiliyor.

**Ne:** Her **başarılı tur sonu** hook’unda, eşikler sağlanırsa **forked query** = ikinci bir LLM oturumu, kısıtlı araç politikası ile.

---

## 2. Bağımlılıklar (kendi projenizde karşılığı)

| cli-claude bileşeni | Rol | Sizin projede karşılığı |
|---------------------|-----|-------------------------|
| `handleStopHooks` → `executeAutoDream` | Tur bittiğinde tetik | “Post-turn”, “after assistant reply”, “on conversation turn complete” hook’u |
| `initAutoDream()` | `runner` closure kurulumu | Servisin bir kez `initialize()` edilmesi |
| `REPLHookContext` | systemPrompt, userContext, systemContext, messages, toolUseContext | Aynı bilgiyi toplayan bir `TurnEndContext` |
| `createCacheSafeParams` + `runForkedAgent` | Parent ile **aynı cache prefix** (opsiyonel optimizasyon) + izole alt context | Ya aynı pattern, ya da basitçe **yeni** API çağrısı (cache paylaşımı olmadan) |
| `createSubagentContext` | Alt ajanın `setAppState` no-op, ayrı `agentId`, klon `readFileState` | Worker process veya sandboxed runner |
| `createAutoMemCanUseTool` | Araç izin matrisi | Policy engine veya tool router |
| `getAutoMemPath`, `isAutoMemoryEnabled` | Hafıza kökü | Sizin `MEMORY_ROOT` config’i |
| `listSessionsTouchedSince` + `getProjectDir` | Transcript dosyalarının mtime ile sayımı | Oturum log dizininiz + `stat` |
| `.consolidate-lock` | Son konsolidasyon zamanı + çoklu süreç kilidi | Aynı dosya veya Redis lock + ayrı `last_run_at` |
| GrowthBook `tengu_onyx_plover` | `minHours`, `minSessions`, `enabled` | Kendi feature flag / env / DB ayarınız |
| `settings.autoDreamEnabled` | Kullanıcı override | Ayarlarınız |

**Uygunluk:** Projenizde zaten (1) **kalıcı hafıza dosyaları**, (2) **tur sonu** lifecycle, (3) **ikinci bir LLM çağrısı** veya worker kuyruğu varsa taşıma doğrudur. Sadece chat API’si, disk yok, araç yoksa bu pattern **ağır ve anlamsız** olur; o zaman sadece “periyodik özet” job’u düşünün.

---

## 3. Tetikleme sözleşmesi (tam sıra)

Kaynak mantık: `autoDream.ts` dosya başı yorumları + `stopHooks.ts`.

### 3.1 Ne zaman `executeAutoDream` çağrılmalı?

- **Sadece ana oturum** (cli-claude: `!toolUseContext.agentId`). Alt ajanların stop hook’unda **çalıştırmayın** (sonsuz/çakışan fork riski).
- **Bare / script modunda** atlayın (kullanıcı “sessiz batch” bekliyor olabilir).
- Fire-and-forget: ana cevap kullanıcıya gittikten sonra arka planda çalışabilir; ana thread’i **bloklamak zorunda değilsiniz** (cli `void executeAutoDream(...)`).

### 3.2 İç kapılar (sıra maliyet düşük → yüksek)

Pseudocode:

```text
function onTurnEnd(ctx):
  if not init_called: return
  if bare_mode: return
  if is_subagent(ctx): return
  if kairos_mode_uses_other_dream: return   // isteğe bağlı ürün kuralı
  if remote_mode: return
  if not auto_memory_enabled: return
  if not feature_auto_dream_enabled: return

  cfg = { minHours: 24, minSessions: 5 }  // remote config’ten oku

  lastAt = read_last_consolidated_at()   // lock file mtime veya 0
  hoursSince = (now - lastAt) / 3600000
  if hoursSince < cfg.minHours: return

  if (now - lastSessionScanAt) < 10 minutes: return
  lastSessionScanAt = now

  sessionIds = list_session_ids_with_transcript_mtime_gt(lastAt)
  sessionIds = filter_out_current_session(sessionIds)
  if sessionIds.length < cfg.minSessions: return

  priorMtime = try_acquire_lock()
  if priorMtime is null: return   // başka canlı süreç veya yarış kaybı

  spawn_consolidation_job(ctx, sessionIds, priorMtime)
```

**Önemli tasarım kararları:**

1. **Zaman eşiği** dosya mtime ile birleşik: başarılı kilitleme anında dosya yazılıyor → yeni `lastAt` = “şimdi”.
2. **Session taraması throttle:** Zaman geçmiş olsa bile her turda dizin taraması yapılmıyor; en fazla 10 dakikada bir.
3. **Mevcut session hariç:** Yoksa her turda “yeterli session” sahte pozitif olur.

---

## 4. Kilit dosyası spesifikasyonu (`.consolidate-lock`)

Konum: `join(MEMORY_ROOT, ".consolidate-lock")` (cli: `getAutoMemPath()` altında).

Semantik:

- **`stat().mtimeMs`** = son başarılı konsolidasyon zamanı (`readLastConsolidatedAt`).
- **Dosya içeriği** = holder PID (string). Canlı PID + “taze” mtime (ör. &lt; 60 dk) → **başka süreç konsolidasyon başlatamaz** (`tryAcquireConsolidationLock` → `null`).
- **Acquire:** `mkdir(MEMORY_ROOT)`, `writeFile(lock, pid)`, tekrar oku; PID kendi PID değilse yarış kaybı → `null`.
- **Başarı:** Lock dosyası güncel mtime ile kalır (yeni `lastAt`).
- **Hata (fork exception) veya kullanıcı kill:** `rollbackConsolidationLock(priorMtime)` — önceki mtime’a `utimes` veya `priorMtime==0` ise `unlink`.

**Taşıma notu:** Redis `SETNX` + TTL ile de yapılabilir; o zaman `lastAt` için ayrı anahtar tutun (mtime trick’i dosya sistemine özgü).

---

## 5. Konsolidasyon prompt’u (içerik sözleşmesi)

Kaynak: `consolidationPrompt.ts` → `buildConsolidationPrompt(memoryRoot, transcriptDir, extra)`.

**Girdiler:**

- `memoryRoot`: mutlak yol (modele verilir).
- `transcriptDir`: JSONL transcript’lerin bulunduğu dizin (grep ile dar arama).
- `extra`: cli’de eklenen **salt okunur bash** kuralı + session ID listesi.

**Dört faz (modele talimat metni olarak):**

1. **Orient:** `ls`, entrypoint dosyası (`ENTRYPOINT_NAME` — projede genelde index), mevcut topic dosyaları, varsa `logs/`, `sessions/`.
2. **Gather:** günlükler, çelişen hafızalar, gerekirse `grep -rn "dar_terim" transcriptDir --include="*.jsonl" | tail -50`.
3. **Consolidate:** topic dosyalarına yaz/güncelle; tarihleri mutlak yap; çelişkiyi düzelt.
4. **Prune and index:** entrypoint’i kısa tut (satır ve KB limitleri prompt’ta sayılı).

**Çıktı:** Kısa özet metin (kullanıcıya / log’a).

Bu prompt’u kendi sisteminizde **sabit string + şablon değişkenleri** olarak saklayın; cli’de GrowthBook’tan bağımsız taşınmış hali `consolidationPrompt.ts` içinde.

---

## 6. Alt ajan / fork çalıştırma sözleşmesi

Kaynak: `autoDream.ts` + `forkedAgent.ts`.

### 6.1 Mesajlar

- `promptMessages`: tek `user` mesajı, içerik = `buildConsolidationPrompt(...)`.
- `initialMessages` = `[...forkContextMessages, ...promptMessages]`  
  Yani parent konuşması **prefix** olarak fork’a ekleniyor → **prompt cache paylaşımı** için (Anthropic cache key: system, tools, model, mesaj prefix’i, thinking config).

### 6.2 İzole tool context

`createSubagentContext`:

- Varsayılan: `setAppState` no-op; `setAppStateForTasks` parent’a yönlendirilir (arka plan görevleri için — cli’de Dream task UI).
- Yeni `agentId`, klonlanmış `readFileState`, child `AbortController` (parent iptal → çocuk iptal).

### 6.3 `skipTranscript: true`

- Sidechain transcript dosyasına yazma yok; `agentId` üretilmez.
- Ephemeral background iş için.

### 6.4 `canUseTool`

`createAutoMemCanUseTool(memoryDir)` davranışı özet:

| Araç | Politika |
|------|----------|
| Read, Grep, Glob | İzin |
| Bash | Sadece `isReadOnly(command)` true ise |
| File Edit / Write | `file_path` `isAutoMemPath(path)` (yani `memoryDir` altında) ise |
| Diğer tüm araçlar | Red + gerekçe mesajı |
| REPL (varsa) | Allow (iç içe primitive yine filtrelenir) |

**Taşıma:** Kendi tool şemanız farklıysa aynı matrisi **isim eşlemesi** ile uygulayın. Önemli olan: **yazmanın sadece hafıza köküne** izin verilmesi.

### 6.5 İlerleme callback’i (`onMessage`)

Her `assistant` mesajında:

- Metin bloklarını birleştir.
- `tool_use` sayısını say.
- `Edit` / `Write` için `input.file_path` topla (bash ile yazılanlar **kaçırılır** — cli bunu dokümante ediyor).

Bu, UI’da “dreaming” progress için.

### 6.6 Tamamlanınca

- Görevi `completed` yap.
- İsteğe bağlı: `appendSystemMessage` ile “Improved / şu dosyalar güncellendi” (sadece `filesTouched.length > 0`).

### 6.7 Hata / abort

- `abortController.signal.aborted` → kullanıcı kill; double-rollback yapma.
- Diğer hatalar: görev `failed`, `rollbackConsolidationLock(priorMtime)`.

---

## 7. Konfigürasyon matrisi

| Anahtar | Varsayılan (cli) | Anlam |
|---------|------------------|--------|
| `minHours` | 24 | Son konsolidasyondan bu kadar saat |
| `minSessions` | 5 | Bu kadar **farklı** session transcript’i güncellenmiş olmalı |
| Session scan interval | 10 dk | Throttle |
| `autoDreamEnabled` | GB `tengu_onyx_plover.enabled` | Kullanıcı `settings` ile override |

---

## 8. Güvenlik ve maliyet

- **Maliyet:** Her tetikte (nadir) tam bir alt ajan döngüsü; tool çağrıları + token.
- **Gizlilik:** Fork’a parent mesajları prefix olarak gider; hassas içerik varsa ya prefix’i kısaltın ya da konsolidasyonu **ayrı model / sıfır context** ile çalıştırın (cache kaybı trade-off).
- **Dosya güvenliği:** `canUseTool` olmadan bu pattern **tehlikeli**; mutlaka path normalizasyonu ve jail root.
- **Çoklu süreç:** Lock + stale PID mantığı şart.

---

## 9. Kendi projenize uyarlama checklist’i

1. **Kalıcı hafıza dizini** tanımlandı mı?
2. **Oturum / transcript** dosyaları diskte mi ve `mtime` ile “aktivite” ölçülebiliyor mu?
3. **Tur sonu** tek bir yerden mi yönetiliyor? (Orada `scheduleMemoryConsolidation()`.)
4. **İkinci LLM runner** var mı? (Aynı SDK ile `query()` döngüsü veya ayrı worker.)
5. **Araç kısıtı** uygulanabiliyor mu?
6. **Feature flag** ve kullanıcı opt-out?
7. **İzlenebilirlik:** log event’leri (`fired`, `completed`, `failed`) ve isteğe bağlı UI task.

Hepsi evet ise: cli-claude ile **yüksek uyumluluk**.

Bir kısmı hayırsa:

- Transcript yok → `minSessions` yerine “son N tur” veya “token birikimi” gibi başka eşik kullanın.
- Fork yok → periyodik cron job + aynı prompt + aynı tool policy (daha basit, cache paylaşımı yok).
- Disk hafızası yok → bu pattern yerine **vectör DB özet job**’u veya “conversation summary” düşünün.

---

## 10. Minimal referans pseudocode (tek dosya mantığı)

```typescript
// types
type ConsolidationConfig = { minHours: number; minSessions: number }

// persisted / remote
let lastSessionScanAt = 0

async function maybeRunMemoryConsolidation(ctx: TurnEndContext, cfg: ConsolidationConfig) {
  if (!gatesOpen(ctx)) return

  const lastAt = await readLastConsolidatedAt(memoryRoot)
  if (hoursSince(lastAt) < cfg.minHours) return

  if (Date.now() - lastSessionScanAt < 10 * 60_000) return
  lastSessionScanAt = Date.now()

  let sessions = await listSessionsTouchedSince(transcriptDir, lastAt)
  sessions = sessions.filter(id => id !== ctx.currentSessionId)
  if (sessions.length < cfg.minSessions) return

  const priorMtime = await tryAcquireConsolidationLock(memoryRoot)
  if (priorMtime === null) return

  const abort = new AbortController()
  const taskId = registerUiTask?.({ kind: 'dream', abort, priorMtime, sessions })

  try {
    const userPrompt = buildConsolidationPrompt(memoryRoot, transcriptDir, buildExtra(ctx, sessions))
    await runSubagent({
      messages: [...ctx.cachePrefixMessages, userMessage(userPrompt)],
      system: ctx.systemPrompt,
      toolsPolicy: autoMemPolicy(memoryRoot),
      signal: abort.signal,
      onAssistantChunk: msg => updateUiTask?.(taskId, msg),
      skipPersistSidechain: true,
    })
    completeUiTask?.(taskId)
    maybeNotifyUser?.(taskId)
  } catch (e) {
    if (abort.signal.aborted) return
    failUiTask?.(taskId)
    await rollbackConsolidationLock(memoryRoot, priorMtime)
  }
}
```

---

## 11. Özet cümle (ürün dili)

Bu özellik, **“boşta kendi kendine düşünen ajan”** değil; **tur sonrası koşullu bir bellek bakım işi**. Başka projeye entegrasyon için kritik parçalar: **tur hook’u**, **hafıza dizini**, **kilit + zaman/session eşikleri**, **kısıtlı araçlı ikinci LLM çağrısı**, **iyi tanımlı konsolidasyon prompt’u**.
