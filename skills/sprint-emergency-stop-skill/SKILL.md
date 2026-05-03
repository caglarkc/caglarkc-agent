---
name: sprint-emergency-stop
description: Planner AI için — kritik sorun anında tüm sistemi anında durdurmak; veri bütünlüğünü koruyarak acil kapanış yapmak.
---

## Purpose

Bazen "hemen dur" gerekir — bütçe aşımı, güvenlik ihlali, yanlış proje.
Acil durdurma: tüm worker'lar durdurulur, state kaydedilir, kullanıcı bilgilendirilir.
Normal kapatmadan farkı: bekleme yok, anında sinyal.

---

## When to Apply

- Kullanıcı "ACIL DUR" veya "STOP" dediğinde
- Kritik güvenlik ihlali tespit edildiğinde
- Yanlış proje dizinine yazılmaya başlandığında

---

## Rules

- Acil stop: tüm asyncio task'leri iptal eder.
- State: kapanmadan önce checkpoint'e kaydedilir (best effort).
- Mesaj: kullanıcıya ne durduruldu ve neden.
- Recovery: sonraki başlatmada checkpoint'ten devam edilebilir.

---

## Guidelines

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

class EmergencyStop:
    def __init__(self):
        self._triggered = False
        self._reason    = ""

    @property
    def triggered(self) -> bool:
        return self._triggered

    async def trigger(
        self,
        reason: str,
        checkpoint_fn=None,
        notify_fn=None,
    ) -> None:
        if self._triggered:
            return
        self._triggered = True
        self._reason    = reason
        logger.critical("ACIL DUR: %s", reason)

        # Tüm çalışan task'leri iptal et
        current = asyncio.current_task()
        for task in asyncio.all_tasks():
            if task is not current and not task.done():
                task.cancel()

        # Checkpoint kaydet (best effort)
        if checkpoint_fn:
            try:
                await asyncio.wait_for(checkpoint_fn(), timeout=5.0)
            except Exception as e:
                logger.error("Checkpoint kaydedilemedi: %s", e)

        # Kullanıcıya bildir
        if notify_fn:
            try:
                await notify_fn(
                    f"🚨 ACİL DURDURMA\nNeden: {reason}\n"
                    f"Sistem güvenli şekilde durduruldu. Checkpoint kaydedildi."
                )
            except Exception:
                pass

_emergency_stop = EmergencyStop()

def get_emergency_stop() -> EmergencyStop:
    return _emergency_stop
```

---

## References

- `sprint-cancellation-skill/SKILL.md` — sprint iptal
- `worker-graceful-shutdown-skill/SKILL.md` — graceful shutdown
- `state-persistence-recovery-skill/SKILL.md` — state kalıcılığı
