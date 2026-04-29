# Operations Guide

## Gunluk Komutlar
- Preflight: `./.venv/bin/python -m scripts.preflight`
- Full health: `./.venv/bin/python -m scripts.healthcheck`
- Fullstack smoke: `./.venv/bin/python -m scripts.smoke_fullstack`
- Backup/restore smoke: `./.venv/bin/python -m scripts.backup_restore_test`
- Load simulation: `./.venv/bin/python -m scripts.load_simulation`
- Daemon start:
  `./.venv/bin/python main.py`
- Daemon start with CLI:
  `./.venv/bin/python main.py --cli`

## Healthcheck Yorumu
- `PROCESS_ALIVE`: PID dosyasindaki proses halen yasiyor mu
- `LAST_HEARTBEAT`: en son worker dispatch/heartbeat zamani
- `STALLED`: daemon sessizlik veya blokaj algiladiysa `True`
- `CHECKPOINT_ACCESS`: LangGraph checkpoint sqlite okunabiliyor mu
- `TELEGRAM`: `configured` ise bot ayarlari tanimli, `disabled` ise kapali
- `OLLAMA`: `healthy`, `model_missing` veya `unreachable:*`

## Log Konumlari
- Uygulama loglari:
  `logs/orchestrator.log`
- systemd append logu:
  `logs/systemd.log`
- Daemon durum dosyasi:
  `data/daemon_status.json`
- State snapshot:
  `data/state_snapshot.json`

## Operasyonel Rutin
1. Deploy oncesi `preflight` kos.
2. Servis kalkinca `healthcheck` ile heartbeat ve checkpoint durumunu gor.
3. Scheduler veya project issue suphelerinde `smoke_fullstack` ve `load_simulation` sonuclarini karsilastir.
4. Kritik restart oncesi sqlite/checkpoint/state snapshot kopyasini al.
