# Faz kabul özeti — tek kaynak

Eski kök dizindeki ayrı `PHASE*_ACCEPTANCE.md` dosyaları kaldırıldı; tüm doğrulama komutları ve kısa garantiler burada özetlenir.

## Komut özeti

| Faz | Doğrulama script'i | Kapsam (kısa) |
|-----|---------------------|----------------|
| 1 | `scripts/check_connections.py` | Sağlayıcılar (LangChain), SQLite checkpointer, minimal graph smoke |
| 1.5 | `scripts/check_phase1_5.py` | Event/approval kontratı, retry, state transaction, GraphManager köprüsü |
| 2 | `scripts/check_phase2.py` | Planner→dispatcher→worker→validator→reviewer, stale/duplicate onay, checkpoint resume |
| 3 | `scripts/check_phase3.py` | Contract/feature gating, rezervasyon, retry/scope-change |
| 4 | `scripts/check_phase4.py` | Reviewer döngüsü, gelişmiş validator, context, stalled/heartbeat |
| 5 | `scripts/check_phase5.py` | Textual CLI, EventBus ↔ UI, `/task`/`/approve`/`/status` |
| 6 | `scripts/check_phase6.py` | Telegram komutları, inline onay, yetkilendirme, notifier |
| 7 | `scripts/check_phase7.py` | `main.py` daemon, graceful shutdown, Ollama gate, recovery (`PYTHONPATH=.`) |
| 8 | `scripts/check_phase8.py` | Çoklu proje, scheduler fairness, CLI/Telegram proje komutları |

**Tek seferde tüm faz script’leri (önerilen):**

```bash
cd /path/to/caglarkc-agent && PYTHONPATH=. .venv/bin/python scripts/run_phase_checks.py
```

**Operasyon / final (ayrı, daha ağır):**

| Amaç | Script |
|------|--------|
| Ön uçuş | `scripts/preflight.py` |
| Uçtan uca akış | `scripts/smoke_fullstack.py` |
| Yedek / geri yükleme | `scripts/backup_restore_test.py` |
| Yük / fairness sanity | `scripts/load_simulation.py` |
| Çalışan süreç özeti | `scripts/healthcheck.py` |

## Faz garantileri (özet)

- **Faz 1**: Altyapı, logging, repository; bağlantı testleri ölçülü PASS/FAIL sözleşmesi (script özet satırları).
- **Faz 1.5**: `EventEnvelope`, onay güvenliği (stale/idempotent), `RetryPolicy`, `StateTransaction`.
- **Faz 2**: `OrchestratorState` omurga düğümleri; onay sonrası resume; checkpoint uyumu.
- **Faz 3**: Contract sprint kapısı dosya rezervasyonu dependency/retry öğrenme scope-change.
- **Faz 4**: Review döngüsü (üst sınır), validator politikaları, context katmanları, stalled sinyalleri.
- **Faz 5**: CLI panel/slash komutları; onay olayları contract-first.
- **Faz 6**: Telegram paralel yüzey; `TELEGRAM_CHAT_ID`; callback güvenliği.
- **Faz 7**: Daemon Tek giriş, geri yükleme, replay-safe kararlar, systemd birimi beklenen alanları.
- **Faz 8**: `ProjectManager` listeleme/arşiv, `FairScheduler`, çok projeli izolasyon.

## Final GO / NO-GO (referans)

Proje daha önce topluca: `preflight`, `smoke_fullstack`, `backup_restore_test`, `load_simulation` ve operasyon dökümanları ile GO kabulü verildi (`docs/DEPLOYMENT_CHECKLIST.md`, `docs/INCIDENT_RUNBOOK.md`). Sayısal eşikler zaman içinde güncellenir; güncel sonuç her zaman ilgili script çıktısıdır — **tek gerçek kaynak**: komut çıktısı ve loglar; bu dosya yalnızca indeks.

## Detaylı faz görevleri

İş görev listesi için: [`plan-phase.md`](../plan-phase.md). Ana vizyon için: [`main-plan.md`](../main-plan.md).

## Worker LLM (gerçek kod üretimi)

Provider eşlemesi, prompt sözleşmesi ve `WORKER_USE_STUB` davranışı: [`REAL_WORKER.md`](REAL_WORKER.md). Birim testi: `tests/test_llm_prompt_build.py`. `pytest` yoksa venv içinde: `pip install -e ".[dev]"` (veya `pip install pytest pytest-asyncio`).
