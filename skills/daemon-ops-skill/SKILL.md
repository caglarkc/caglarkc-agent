---
name: daemon-ops
description: AI Development Team Orchestrator projesinin 7/24 daemon olarak çalıştırılması. systemd service kurulumu, otomatik başlatma, crash recovery, log yönetimi, deployment adımları. Daemon kurulumu veya deployment kodu yazarken referans alınır.
---

## systemd Service

```ini
# ai-orchestrator.service
[Unit]
Description=AI Development Team Orchestrator
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=<kullanici_adi>
WorkingDirectory=/path/to/ai-orchestrator
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Ortam değişkenleri
EnvironmentFile=/path/to/ai-orchestrator/.env

# Loglar
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-orchestrator

[Install]
WantedBy=multi-user.target
```

### Kurulum Komutları

```bash
# Service dosyasını kopyala
sudo cp ai-orchestrator.service /etc/systemd/system/

# systemd'yi yenile
sudo systemctl daemon-reload

# Başlat ve otomatik başlatmayı aktif et
sudo systemctl enable ai-orchestrator
sudo systemctl start ai-orchestrator

# Durum kontrolü
sudo systemctl status ai-orchestrator

# Log takibi
sudo journalctl -u ai-orchestrator -f
```

---

## Crash Recovery Stratejisi

### systemd Seviyesi
- `Restart=always` — her çöküşte yeniden başlar
- `RestartSec=10` — 10 saniye bekle (API rate limit vs.)
- `StartLimitBurst=3` — 60 saniyede max 3 restart

### Uygulama Seviyesi
CrewAI Flow persistence ile kaldığı yerden devam eder:

```python
# main.py
async def main():
    # Başlangıçta bekleyen flow'ları recover et
    flow_manager = FlowManager()
    await flow_manager.recover_pending_flows()

    # Normal başlatma devam eder
    await asyncio.gather(
        telegram.start(),
        flow_manager.listen(),
        keep_alive()
    )
```

### State Recovery
```python
# src/core/flow_manager.py
async def recover_pending_flows(self):
    logger.info("Bekleyen flow'lar kontrol ediliyor...")
    try:
        pending = await self.persistence.get_all_pending()
        if not pending:
            logger.info("Bekleyen flow yok.")
            return
        for flow_state in pending:
            logger.info(f"Flow recover ediliyor: {flow_state.flow_id}")
            asyncio.create_task(self._recover_flow(flow_state))
    except Exception as e:
        logger.error(f"Recovery hatası: {e}")

async def _recover_flow(self, flow_state):
    try:
        flow = OrchestratorFlow.from_pending(
            flow_id=flow_state.flow_id,
            persistence=self.persistence
        )
        # Kullanıcıya bildir — sistem yeniden başladı
        await self.bus.emit("system.recovered", {
            "flow_id": flow_state.flow_id,
            "message": "Sistem yeniden başladı. Onay bekleniyor."
        })
    except Exception as e:
        logger.error(f"Flow {flow_state.flow_id} recover edilemedi: {e}")
```

---

## Log Yönetimi

```python
# src/config/logging_config.py
import logging
import logging.handlers
from rich.logging import RichHandler
from pathlib import Path

def setup_logging(level: str = "INFO"):
    Path("logs").mkdir(exist_ok=True)

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Console (Rich formatı)
    console = RichHandler(rich_tracebacks=True, show_time=True)
    console.setLevel(level)

    # Dosya (rotate — max 10MB, 5 dosya)
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/orchestrator.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    ))

    root.addHandler(console)
    root.addHandler(file_handler)
```

---

## Ollama Bağımlılığı

Sistem Ollama'ya bağımlı olduğundan service tanımına eklenir:

```ini
After=network.target ollama.service
Wants=ollama.service
```

Ollama yoksa sistemin beklemesi için health check:

```python
async def check_ollama_health() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_HOST}/api/tags",
                timeout=5.0
            )
            return response.status_code == 200
    except Exception:
        return False

async def wait_for_ollama(max_wait: int = 60):
    logger.info("Ollama bekleniyor...")
    for i in range(max_wait):
        if await check_ollama_health():
            logger.info("Ollama hazır.")
            return
        await asyncio.sleep(1)
    raise RuntimeError("Ollama başlatılamadı")
```

---

## Deployment Checklist

Yeni kurulum veya güncelleme öncesi:

```
[ ] .env dosyası dolu ve doğru
[ ] GEMINI_API_KEY geçerli
[ ] OPENROUTER_API_KEY_1 ve _2 geçerli
[ ] TELEGRAM_BOT_TOKEN geçerli
[ ] TELEGRAM_CHAT_ID doğru
[ ] OLLAMA_HOST erişilebilir
[ ] OLLAMA_MODEL indirilmiş (ollama pull qwen2.5-coder)
[ ] PROJECTS_DIR mevcut ve yazılabilir
[ ] logs/ klasörü mevcut
[ ] storage/ klasörü mevcut
[ ] pyproject.toml bağımlılıkları kurulu
[ ] systemd service aktif
```

---

## Güncelleme Prosedürü

```bash
# Servisi durdur
sudo systemctl stop ai-orchestrator

# Kodu güncelle
git pull origin main

# Bağımlılıkları güncelle (kullanıcı tarafında)
uv sync

# Servisi başlat
sudo systemctl start ai-orchestrator

# Log kontrol
sudo journalctl -u ai-orchestrator -f --since "1 minute ago"
```

---

## References

- `python-async-patterns/SKILL.md` — crash recovery async pattern'ları
- `project-architecture/SKILL.md` — klasör yapısı, env değişkenleri