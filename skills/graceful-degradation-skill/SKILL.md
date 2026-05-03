---
name: graceful-degradation
description: Coder AI için — bir bileşen başarısız olduğunda sistemin azaltılmış işlevsellikle çalışmaya devam etmesini sağlamak; tam çöküşü önlemek.
---

## Purpose

Telegram çalışmıyorsa CLI'dan devam edilebilir.
Gemini cevap vermiyorsa Ollama ile devam edilebilir.
Graceful degradation, kısmi arızada sistemi ayakta tutar.

---

## When to Apply

- Opsiyonel bileşen başarısız olduğunda
- Provider fallback zinciri kurulurken
- Notification servisi erişilemez olduğunda

---

## Rules

- Kritik bileşen: fail → system down (kabul edilebilir).
- Opsiyonel bileşen: fail → degraded mode + uyarı log.
- Degraded mode: kısıtlı işlevsellik, kullanıcı bilgilendirilir.
- Recovery: bileşen tekrar erişilebilir olunca otomatik.

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class SystemCapabilities:
    llm_available: bool = True
    telegram_available: bool = True
    db_available: bool = True
    
    @property
    def can_run_sprint(self) -> bool:
        return self.llm_available and self.db_available
    
    @property
    def can_notify(self) -> bool:
        return self.telegram_available
    
    def degraded_features(self) -> list[str]:
        features = []
        if not self.telegram_available:
            features.append("Telegram bildirimleri devre dışı")
        return features

async def check_and_degrade(settings: Settings) -> SystemCapabilities:
    caps = SystemCapabilities()
    
    # Telegram kontrolü
    if settings.telegram_bot_token:
        try:
            await asyncio.wait_for(ping_telegram(settings), timeout=3.0)
        except Exception:
            caps.telegram_available = False
            logger.warning("Telegram erişilemez — CLI modunda devam")
    
    return caps

# Notification ile graceful degradation
async def notify_user(
    message: str,
    caps: SystemCapabilities,
    notifier: NotificationService,
) -> None:
    if caps.can_notify:
        try:
            await notifier.send(message)
            return
        except Exception:
            logger.warning("Telegram bildirimi başarısız — CLI'ya düşüyor")
    
    # Fallback: sadece log
    logger.info(f"[BILDIRIM - CLI] {message}")
```

---

## References

- `provider-fallback-chain-skill/SKILL.md` — LLM fallback
- `notification-abstraction-skill/SKILL.md` — bildirim soyutlama
- `healthcheck-endpoint-skill/SKILL.md` — sağlık kontrolü
