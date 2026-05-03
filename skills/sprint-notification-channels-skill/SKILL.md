---
name: sprint-notification-channels
description: Planner AI için — sprint bildirimlerini farklı kanallara (CLI, Telegram, log) yönlendirmek; kanal seçimini yapılandırılabilir tutmak.
---

## Purpose

Bildirim tek bir kanala sabitlenirse başka ortamda çalışmaz.
Çok kanallı bildirim: aynı mesaj CLI, Telegram veya sadece log'a gidebilir.
Kanal seçimi: ortam değişkeni veya kullanıcı tercihi.

---

## When to Apply

- Sprint tamamlandığında kullanıcıya bildirim gönderilirken
- Onay isteği iletilirken
- Hata bildirimi yapılırken

---

## Rules

- Kanal listesi: `NOTIFICATION_CHANNELS` env değişkeninden okunur.
- Varsayılan: sadece CLI (stdout).
- Telegram: token + chat_id gerekli — yoksa skip.
- Bildirim başarısız: sprint durdurmaz, log + fallback.

---

## Guidelines

```python
import os
import asyncio
from typing import Protocol

class NotificationChannel(Protocol):
    async def send(self, message: str) -> bool: ...

class CLIChannel:
    async def send(self, message: str) -> bool:
        print(f"\n[Bildirim] {message}")
        return True

class TelegramChannel:
    def __init__(self, token: str, chat_id: str):
        self._token   = token
        self._chat_id = chat_id
    
    async def send(self, message: str) -> bool:
        import aiohttp
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={
                    "chat_id": self._chat_id,
                    "text": message,
                }, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return resp.status == 200
        except Exception:
            return False

class LogChannel:
    async def send(self, message: str) -> bool:
        import logging
        logging.getLogger("notifications").info(message)
        return True

def build_channels() -> list[NotificationChannel]:
    channels: list[NotificationChannel] = [CLIChannel()]
    
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        channels.append(TelegramChannel(token, chat_id))
    
    channels.append(LogChannel())
    return channels

async def notify_all(channels: list[NotificationChannel], message: str) -> None:
    await asyncio.gather(
        *[ch.send(message) for ch in channels],
        return_exceptions=True,
    )
```

---

## References

- `notification-abstraction-skill/SKILL.md` — bildirim soyutlama
- `telegram-command-handler-skill/SKILL.md` — Telegram komut işleyici
- `sprint-stakeholder-update-skill/SKILL.md` — paydaş güncellemesi
