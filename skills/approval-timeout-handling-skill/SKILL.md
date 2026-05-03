---
name: approval-timeout-handling
description: Planner AI için — HITL onay bekleme süresi aşıldığında ne yapılacağını belirlemek; timeout sonrası kullanıcıyı hatırlatmak veya planı iptal etmek.
---

## Purpose

Kullanıcı onay vermeden giderse sprint askıda kalır.
Timeout mekanizması süresi dolan planları temizler veya hatırlatma gönderir.
Askıda kalan sprint'ler kaynak israfı yaratır.

---

## When to Apply

- HITL interrupt_before=["dispatcher"] kullanıldığında
- Onay bekleme daemon başladığında
- Uzun süreli askıda sprint kontrolü eklenirken

---

## Rules

- Timeout: 24 saat (konfigüre edilebilir).
- Timeout öncesi: Telegram/CLI hatırlatma gönderilir.
- Timeout sonrası: sprint `cancelled` yapılır.
- Kullanıcı zamanında dönerse normal akış devam eder.

---

## Guidelines

```python
import asyncio
from datetime import datetime, timedelta

APPROVAL_TIMEOUT_HOURS = 24

async def wait_for_approval_with_timeout(
    project_id: str,
    approval_event: asyncio.Event,
    notification_service,
) -> bool:
    """Returns True if approved, False if timed out."""
    timeout_seconds = APPROVAL_TIMEOUT_HOURS * 3600
    
    # 1 saat kala hatırlatma
    reminder_delay = timeout_seconds - 3600
    
    async def send_reminder():
        await asyncio.sleep(reminder_delay)
        if not approval_event.is_set():
            await notification_service.send(
                f"Sprint planı onay bekliyor. "
                f"1 saat içinde yanıt vermezseniz iptal edilecek."
            )
    
    reminder_task = asyncio.create_task(send_reminder())
    
    try:
        await asyncio.wait_for(
            approval_event.wait(),
            timeout=timeout_seconds
        )
        reminder_task.cancel()
        return True
    except asyncio.TimeoutError:
        reminder_task.cancel()
        logger.warning(f"Onay timeout: {project_id}")
        return False

async def handle_approval_timeout(
    project_id: str,
    repo: ProjectRepository
) -> None:
    sprint = await repo.get_active_sprint(project_id)
    if sprint:
        await repo.update_sprint_status(sprint.sprint_id, "cancelled")
        logger.info(f"Sprint timeout ile iptal edildi: {sprint.sprint_id}")
```

---

## References

- `interrupt-before-node-skill/SKILL.md` — HITL
- `sprint-lifecycle-state-machine-skill/SKILL.md` — sprint durumu
- `telegram-bot-patterns-skill/SKILL.md` — bildirim
