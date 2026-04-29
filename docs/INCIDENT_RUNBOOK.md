# Incident Runbook

## 1. Stuck Queue
Belirti:
- `healthcheck` icinde `STALLED=True`
- yeni `sprint.worker_done` event'i gelmiyor

Adimlar:
1. `./.venv/bin/python -m scripts.healthcheck`
2. `logs/orchestrator.log` icinde son `system.stalled` ve `dispatch_blocked` kayitlarini kontrol et.
3. `./.venv/bin/python -m scripts.backup_restore_test` ile checkpoint/state restore zincirini hizlica dogrula.
4. Orphan reservation supheli ise daemon restart et; Faz 7 cleanup rezervasyon reclaim eder.

## 2. Provider Down
Belirti:
- Ollama preflight veya daemon start gate fail
- rate-limit veya provider time-out loglari artiyor

Adimlar:
1. `./.venv/bin/python -m scripts.preflight`
2. `OLLAMA` sonucunu kontrol et.
3. Gerekirse remote provider key'leriyle degrade mode kullan.
4. `./.venv/bin/python -m scripts.load_simulation` ile throttle/fairness davranisini tekrar gor.

## 3. Stale Approval
Belirti:
- CLI/Telegram onayinda “Bu onay artik gecerli degil”

Adimlar:
1. Approval event timestamp ve approval request timeout'unu kontrol et.
2. `data/state_snapshot.json` icinde ilgili `active_approval_id` var mi bak.
3. Gerekirse yeni task ile planner'dan taze approval olustur.

## 4. Replay / Duplicate Event
Belirti:
- ayni approval ikinci kez tiklandi
- beklenmeyen tekrar resume supheleri

Adimlar:
1. `logs/orchestrator.log` icinde `duplicate_event_id` veya `duplicate_idempotency_key` kaydini ara.
2. `GraphManager` replay-safe davranisi aktifse ikinci islem `no-op` olmalidir.
3. Suphede `./.venv/bin/python -m scripts.check_phase7` kos; replay-safe acceptance bunu dogrular.

## 5. Restore Sonrasi Resume Calismiyor
Belirti:
- daemon recovery var ama pending thread devam etmiyor

Adimlar:
1. `./.venv/bin/python -m scripts.backup_restore_test`
2. `data/langgraph_checkpoints.sqlite` ve `data/state_snapshot.json` dosyalarinin tarihlerini kontrol et.
3. `system.recovered` event'i loglandi mi bak.
4. Approval request recover olduysa yeni karar event'iyle resume tetikle.
