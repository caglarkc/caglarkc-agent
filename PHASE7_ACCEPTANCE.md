# Phase 7 Acceptance

## Uygulanan Davranislar
- `main.py` ile tek entrypoint kuruldu; startup sirasi `config -> storage -> graph -> interfaces`.
- `GraphManager` daemon runtime, checkpoint recovery, replay-safe approval handling ve orphan reservation cleanup kazandi.
- Graceful shutdown akisi SIGINT/SIGTERM ile state snapshot, checkpoint runtime ve interface kapatisini kontrollu yapiyor.
- Ollama startup gate retry/backoff ile calisiyor; remote provider varsa degrade mode'a gecebilir.
- `scripts/healthcheck.py` process, heartbeat, stalled, checkpoint, Telegram ve Ollama ozetini deterministic formatta uretiyor.
- `ai-orchestrator.service` systemd icin `Restart=on-failure` ve 10 saniye gecikme ile hazirlandi.

## Gecen Testler
- daemon bootstrap
- graceful shutdown
- ollama health gate
- crash recovery + checkpoint resume
- orphan reserved cleanup
- replay-safe duplicate event korumasi
- healthcheck output
- systemd unit temel kontrolleri

## Faz 8'e Devredilen Garantiler
- restart sonrasi pending thread ve approval durumu tekrar okunabiliyor
- stale/duplicate kararlar graph'i yanlislikla tekrar ilerletmiyor
- orphan `reserved` dosyalar temizleniyor
- daemon saglik durumu diskten okunabilir halde tutuluyor
- multi-project scheduler eklenirken stabil bir runtime omurgasi hazir
