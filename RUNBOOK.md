# AI Orchestrator Runbook

Bu dosya bu projeyi lokalden calistirmak, CLI ile task/resume test etmek ve temel kontrolleri yapmak icin tek kaynak.

## En Onemli Komut

CLI ile lokal test icin bunu kullan:

```bash
./.venv/bin/python main.py --cli --no-telegram
```

Neden bu komut:
- `main.py` gercek daemon entrypoint.
- `--cli` Textual CLI ekranini acar.
- `--no-telegram` Telegram botunu bu lokal testte kapatir; sadece CLI akisini test edersin.

## Diger Baslatma Komutlari

Daemon'u CLI acmadan baslat:

```bash
./.venv/bin/python main.py --no-telegram
```

Daemon'u CLI + Telegram ile baslat:

```bash
./.venv/bin/python main.py --cli
```

Help'i gor:

```bash
./.venv/bin/python main.py --help
```

Systemd servis dosyasi:

```bash
ai-orchestrator.service
```

Bu servis su an CLI acmadan daemon baslatir:

```bash
./.venv/bin/python main.py
```

## Yeni Ana CLI Akisi

CLI'yi ac:

```bash
./.venv/bin/python main.py --cli --no-telegram
```

CLI icinde provider durumunu kontrol et:

```text
/scan
```

Beklenen: `gemini ... available=True` veya Gemini icin api key set/available bilgisi.

Projeleri gor:

```text
/projects
```

Yeni proje/sohbet baslat:

```text
/new CaglarKc NutritionApp
```

Projeyi anlatmaya devam et:

```text
/r Kullanici gunluk kalori ve makro takibi yapacak
/r Premium uyelikte haftalik beslenme raporu olacak
/r Mobil oncelikli sade bir uygulama istiyorum
```

Beklenen:

```text
Message queued [thread-...]: ...
```

Durumu kontrol et:

```text
/status
```

Beklenen:
- `thread-...` task ID olarak gorunur.
- Gemini manager cevap verir.
- `/plan` demedigin icin worker/sprint baslamaz.
- Durum `draft_ready`, `needs_input` veya planlama durumunda kalir.

CLI'yi kapat:

```text
Ctrl+C
```

Tekrar ac:

```bash
./.venv/bin/python main.py --cli --no-telegram
```

Ayni projeye/sohbete devam et:

```text
/resume
/r Renkleri sade tut, onboarding cok kisa olsun
```

Beklenen:
- Yeni `thread-...` uretmez.
- Onceki task ile ayni thread ID devam eder.
- Gemini onceki konusma ve draft plani hatirlayarak cevap verir.

Belirli projeyi resume et:

```text
/resume CaglarKc NutritionApp
```

veya:

```text
/resume <project_id>
```

Sohbetten plana gecmek icin:

```text
/plan CaglarKc NutritionApp
```

Beklenen:
- `Planning requested [thread-...]`
- Approval panelde approval ID olusur.
- Sistem onay bekler; worker akisi onaysiz baslamaz.

Onayla:

```text
/approve
```

veya:

```text
/approve <approval_id>
```

Reddet:

```text
/reject <approval_id> <neden>
```

Iptal et:

```text
/cancel <approval_id> <neden>
```

Aktif planning task'ini approval olmadan kapat:

```text
/close <neden>
```

Approval yokken aktif planning task'ini reddet:

```text
/reject <neden>
```

Approval yokken aktif planning task'ini iptal et:

```text
/cancel <neden>
```

Bu komutlardan sonra sonraki `/r ...` veya legacy `/task ...` yeni `thread-...` ile baslar.

## CLI Komutlari

```text
/task <metin>
/new <proje adi>
/resume [project_id veya proje adi]
/r <mesaj>
/plan [project_id veya proje adi]
/apply [istege bagli not]
/status
/approve [approval_id]
/reject [approval_id] [reason]
/cancel [approval_id] [reason]
/close [reason]
/projects
/history <proje>
/project use <id veya proje adi>
/scan
/help
```

Not: `/task` eski alias olarak duruyor. Yeni ana sohbet komutu `/r`.

## Saglik ve Test Komutlari

Tum unit/integration testleri:

```bash
./.venv/bin/python -m pytest -q
```

Preflight:

```bash
./.venv/bin/python -m scripts.preflight
```

Healthcheck:

```bash
./.venv/bin/python -m scripts.healthcheck
```

Fullstack smoke:

```bash
./.venv/bin/python -m scripts.smoke_fullstack
```

Backup/restore smoke:

```bash
./.venv/bin/python -m scripts.backup_restore_test
```

Load simulation:

```bash
./.venv/bin/python -m scripts.load_simulation
```

Phase check toplu kosum:

```bash
./.venv/bin/python -m scripts.run_phase_checks
```

## Dosya Konumlari

Log:

```text
logs/orchestrator.log
```

Systemd append log:

```text
logs/systemd.log
```

Daemon PID:

```text
data/ai-orchestrator.pid
```

Daemon status:

```text
data/daemon_status.json
```

State snapshot:

```text
data/state_snapshot.json
```

LangGraph checkpoint:

```text
data/langgraph_checkpoints.sqlite
```

## Basari Kriteri

Bu akis basarili sayilir:

1. `./.venv/bin/python main.py --cli --no-telegram` CLI'yi acar.
2. `/new CaglarKc NutritionApp` kullanici isimli proje olusturur.
3. `/r ...` sana `thread-...` ID dondurur.
4. CLI kapat/ac sonrasi `/resume` ve `/r ...` ayni thread ID ile devam eder.
5. Gemini onceki konusmayi ve draft plani hatirlar.
6. `/plan CaglarKc NutritionApp` approval olusturur ve bekler.
7. `/approve` sonrasi worker akisi baslar.

## Notlar

- `pyproject.toml` icinde CLI console script yok; bu yuzden dogrudan `main.py` calistiriliyor.
- `smoke-test` adli console script sadece `scripts.check_connections:main` icin tanimli.
- Systemd servisi CLI acmaz; arka plan daemon icindir.
