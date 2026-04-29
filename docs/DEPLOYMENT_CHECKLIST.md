# Deployment Checklist

## Konfig
- [ ] `.env` dosyasi mevcut
- [ ] `OLLAMA_BASE_URL` ve `OLLAMA_MODEL` dogru
- [ ] Gerekliyse `GEMINI_API_KEY` / `OPENROUTER_API_KEY_*` tanimli
- [ ] Gerekliyse `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` birlikte tanimli

## Dosya ve Servis
- [ ] `data/` ve `logs/` yazilabilir
- [ ] `ai-orchestrator.service` icindeki `WorkingDirectory`, `EnvironmentFile`, `ExecStart` dogru host path'lerine bakiyor
- [ ] `systemctl daemon-reload` yapildi
- [ ] `systemctl enable ai-orchestrator.service` hazir

## Dogrulama
- [ ] `./.venv/bin/python -m scripts.preflight`
- [ ] `./.venv/bin/python -m scripts.smoke_fullstack`
- [ ] `./.venv/bin/python -m scripts.backup_restore_test`
- [ ] `./.venv/bin/python -m scripts.load_simulation`
- [ ] `./.venv/bin/python -m scripts.healthcheck`

## Go-Live Oncesi Son Bakis
- [ ] `healthcheck` icinde `CHECKPOINT_ACCESS=True`
- [ ] `healthcheck` icinde `OLLAMA=healthy` veya degrade plan bilerek kabul edildi
- [ ] `load_simulation` icinde starvation yok
- [ ] operasyon ekibi `OPERATIONS.md` ve `INCIDENT_RUNBOOK.md` dosyalarina erisiyor
