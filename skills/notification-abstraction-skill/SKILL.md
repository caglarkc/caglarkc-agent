---
name: notification-abstraction
description: Coder AI için — Telegram ve CLI gibi farklı bildirim kanallarını soyutlayan ortak interface yazmak; kanal değişimini kolaylaştırmak.
---

## Purpose

Telegram'a doğrudan bağlı kod, Telegram değiştiğinde kırılır.
Notification interface, kanalı değiştirmeyi kolaylaştırır.
Test'te mock notification kullanılır.

---

## When to Apply

- Bildirim gönderme kodu yazılırken
- Yeni bildirim kanalı (email, webhook) eklenmesi gerektiğinde
- Notification sistemi test edilirken

---

## Rules

- `NotificationService` abstract base class (ABC).
- Her kanal ayrı implementasyon: `TelegramNotifier`, `CLINotifier`.
- `send(message)` ve `send_approval_request(plan)` zorunlu metodlar.
- Test için `MockNotifier`.

---

## Guidelines

```python
from abc import ABC, abstractmethod

class NotificationService(ABC):
    @abstractmethod
    async def send(self, message: str) -> None: ...
    
    @abstractmethod
    async def send_approval_request(
        self,
        plan_summary: str,
        sprint_id: str,
    ) -> None: ...

class TelegramNotifier(NotificationService):
    def __init__(self, bot_token: str, chat_id: str):
        self._token = bot_token
        self._chat_id = chat_id
    
    async def send(self, message: str) -> None:
        from telegram import Bot
        bot = Bot(token=self._token)
        await bot.send_message(chat_id=self._chat_id, text=message)
    
    async def send_approval_request(
        self, plan_summary: str, sprint_id: str
    ) -> None:
        msg = (
            f"Sprint planı hazır: {sprint_id}\n\n"
            f"{plan_summary}\n\n"
            f"Onaylamak için: /approve\n"
            f"Reddetmek için: /reject <gerekçe>"
        )
        await self.send(msg)

class CLINotifier(NotificationService):
    async def send(self, message: str) -> None:
        print(f"\n[BILDIRIM] {message}")
    
    async def send_approval_request(
        self, plan_summary: str, sprint_id: str
    ) -> None:
        print(f"\n[ONAY GEREKLİ] Sprint: {sprint_id}\n{plan_summary}")

class MockNotifier(NotificationService):
    def __init__(self):
        self.sent_messages: list[str] = []
    
    async def send(self, message: str) -> None:
        self.sent_messages.append(message)
    
    async def send_approval_request(self, plan: str, sprint_id: str) -> None:
        self.sent_messages.append(f"APPROVAL:{sprint_id}:{plan}")
```

---

## References

- `telegram-bot-patterns-skill/SKILL.md` — Telegram pattern
- `telegram-command-handler-skill/SKILL.md` — komut handler
- `dependency-injection-patterns-skill/SKILL.md` — DI
