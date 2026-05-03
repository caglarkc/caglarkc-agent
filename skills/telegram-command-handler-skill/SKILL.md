---
name: telegram-command-handler
description: Coder AI için — python-telegram-bot ile Telegram komutlarını (/start, /status, /approve) işleyen handler'lar yazmak.
---

## Purpose

Telegram arayüzü, kullanıcının mobil cihazdan agent'ı yönetmesini sağlar.
Her komut ayrı handler'a bağlanır; komut dışı mesajlar ayrıca işlenir.
HITL akışındaki onay/ret kararları Telegram'dan alınabilir.

---

## When to Apply

- `src/interfaces/telegram/handlers.py` yazılırken
- Yeni Telegram komutu eklenmesi gerektiğinde
- Onay akışı Telegram'a bağlanırken

---

## Rules

- Her handler: `async def handler(update, context)` imzası.
- Hata durumunda kullanıcıya Türkçe hata mesajı gönderilir.
- Uzun işlemler: önce "İşleniyor..." mesajı gönderilir.
- Handler, EventBus'a event emit eder — doğrudan iş yapmaz.
- Bot token: Settings'ten alınır — hard-code edilmez.

---

## Guidelines

```python
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text(
        "Merhaba! Agent hazır.\n"
        "Komutlar:\n"
        "/status — Mevcut sprint durumu\n"
        "/approve — Planı onayla\n"
        "/reject <gerekçe> — Planı reddet"
    )

async def status_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text("İşleniyor...")
    # EventBus'a sorgu emit et
    await event_bus.emit("telegram.status_requested", {
        "chat_id": update.message.chat_id
    })

async def approve_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    await event_bus.emit("user.approval", {
        "approved": True,
        "source": "telegram",
        "chat_id": update.message.chat_id,
    })
    await update.message.reply_text("Onay alındı, sprint başlıyor...")

async def reject_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    reason = " ".join(context.args) if context.args else "Gerekçe belirtilmedi"
    await event_bus.emit("user.approval", {
        "approved": False,
        "reason": reason,
        "source": "telegram",
    })
    await update.message.reply_text(f"Red kaydedildi: {reason}")

def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("approve", approve_handler))
    app.add_handler(CommandHandler("reject", reject_handler))
    return app
```

---

## References

- `telegram-bot-patterns-skill/SKILL.md` — bot genel pattern
- `event-emission-pattern-skill/SKILL.md` — event emit
- `pm-mode-skill/SKILL.md` — onay workflow
