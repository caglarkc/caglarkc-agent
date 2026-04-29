---
name: telegram-bot-patterns
description: AI Development Team Orchestrator projesinde Telegram bot ve CLI arayüzü entegrasyon kuralları. python-telegram-bot async yapısı, EventBus entegrasyonu, Flow resume pattern'ı, onay mekanizması, CLI Textual yapısı. Telegram veya CLI kodu yazarken referans alınır.
---

## Telegram Bot Yapısı

```python
# src/interfaces/telegram/bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from src.core.event_bus import EventBus
from src.config.settings import settings

class TelegramBot:
    def __init__(self):
        self.app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        self.bus = EventBus()
        self._setup_handlers()
        self._setup_bus_listeners()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("task", self.handle_task))
        self.app.add_handler(CommandHandler("status", self.handle_status))
        self.app.add_handler(CommandHandler("cancel", self.handle_cancel))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    def _setup_bus_listeners(self):
        # CrewAI'dan gelen event'leri Telegram'a yönlendir
        self.bus.subscribe("plan.approval_needed", self.send_plan_for_approval)
        self.bus.subscribe("sprint.completed", self.send_sprint_summary)
        self.bus.subscribe("error.occurred", self.send_error_alert)
        self.bus.subscribe("project.completed", self.send_project_complete)

    async def start(self):
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop(self):
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
```

---

## Komutlar

```python
async def handle_task(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Güvenlik: sadece yetkili chat
    if update.effective_chat.id != settings.TELEGRAM_CHAT_ID:
        return

    task_text = " ".join(ctx.args)
    if not task_text:
        await update.message.reply_text("Kullanım: /task <proje açıklaması>")
        return

    await update.message.reply_text("⏳ Görev alındı, analiz ediliyor...")
    await self.bus.emit("task.received", {"text": task_text, "source": "telegram"})

async def handle_status(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    state = await self.state_manager.get("active_project")
    if not state:
        await update.message.reply_text("Aktif proje yok.")
        return
    await update.message.reply_text(self._format_status(state))

async def handle_cancel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await self.bus.emit("task.cancelled", {"source": "telegram"})
    await update.message.reply_text("❌ Görev iptal edildi.")
```

---

## Onay Mekanizması (Inline Keyboard)

```python
async def send_plan_for_approval(self, data: dict):
    plan_text = data["plan"]
    flow_id = data["flow_id"]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Onayla", callback_data=f"approve:{flow_id}"),
            InlineKeyboardButton("❌ İptal", callback_data=f"reject:{flow_id}"),
        ],
        [
            InlineKeyboardButton("✏️ Revize Et", callback_data=f"revise:{flow_id}")
        ]
    ])

    await self.app.bot.send_message(
        chat_id=settings.TELEGRAM_CHAT_ID,
        text=f"📋 *Sprint Planı*\n\n{plan_text}\n\nOnaylıyor musunuz?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def handle_callback(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, flow_id = query.data.split(":", 1)

    if action == "approve":
        await query.edit_message_text("✅ Onaylandı, sprint başlıyor...")
        await self.bus.emit("plan.approved", {"flow_id": flow_id})

    elif action == "reject":
        await query.edit_message_text("❌ İptal edildi.")
        await self.bus.emit("plan.rejected", {"flow_id": flow_id})

    elif action == "revise":
        await query.edit_message_text("✏️ Revizyon notunu yazın:")
        # Bir sonraki mesajı revizyon notu olarak al
        ctx.user_data["awaiting_revision"] = flow_id
```

---

## Flow Resume

Telegram onayı gelince CrewAI Flow kaldığı yerden devam eder:

```python
# src/core/flow_manager.py
from crewai.flow.persistence.sqlite import SQLiteFlowPersistence
from src.crew.flow import OrchestratorFlow

class FlowManager:
    def __init__(self):
        self.persistence = SQLiteFlowPersistence(db_path="./storage/flow_state.db")
        self.bus = EventBus()
        self.bus.subscribe("plan.approved", self.on_plan_approved)
        self.bus.subscribe("plan.rejected", self.on_plan_rejected)

    async def on_plan_approved(self, data: dict):
        flow_id = data["flow_id"]
        flow = OrchestratorFlow.from_pending(
            flow_id=flow_id,
            persistence=self.persistence
        )
        await flow.resume(feedback="approved")

    async def on_plan_rejected(self, data: dict):
        flow_id = data["flow_id"]
        flow = OrchestratorFlow.from_pending(
            flow_id=flow_id,
            persistence=self.persistence
        )
        await flow.resume(feedback="rejected")
```

---

## CLI Yapısı (Textual)

```python
# src/interfaces/cli/app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Static, Input
from textual.containers import Horizontal, Vertical
from src.core.event_bus import EventBus

class OrchestratorCLI(App):
    CSS = """
    #task-panel { width: 30%; border: solid green; }
    #log-panel { width: 70%; border: solid blue; }
    #approval-panel { height: 10; border: solid yellow; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="task-panel"):
                yield Static("Aktif Görevler", id="tasks-title")
                yield Static("", id="tasks-content")
            with Vertical(id="log-panel"):
                yield RichLog(id="log-output", highlight=True)
        yield Static("", id="approval-panel")
        yield Input(placeholder="/task <açıklama> veya /status", id="cmd-input")
        yield Footer()

    async def on_mount(self):
        bus = EventBus()
        bus.subscribe("sprint.completed", self.on_sprint_event)
        bus.subscribe("plan.approval_needed", self.show_approval_prompt)
        bus.subscribe("error.occurred", self.show_error)

    async def on_input_submitted(self, event: Input.Submitted):
        cmd = event.value.strip()
        self.query_one("#cmd-input", Input).clear()

        if cmd.startswith("/task "):
            task_text = cmd[6:]
            await EventBus().emit("task.received", {
                "text": task_text,
                "source": "cli"
            })
        elif cmd == "/status":
            await self.show_status()

    async def on_sprint_event(self, data: dict):
        log = self.query_one("#log-output", RichLog)
        log.write(f"[green]✅ Sprint tamamlandı: {data['sprint_id']}[/green]")

    async def show_approval_prompt(self, data: dict):
        panel = self.query_one("#approval-panel", Static)
        panel.update(
            f"[yellow]⚠️ ONAY GEREKLİ[/yellow]\n"
            f"{data['plan'][:200]}...\n"
            f"Onayla: /approve | İptal: /reject"
        )
```

---

## Bildirim Formatları

```python
# src/interfaces/telegram/notifier.py

def format_sprint_summary(sprint: dict) -> str:
    return (
        f"✅ *Sprint {sprint['number']} Tamamlandı*\n\n"
        f"👥 Worker'lar:\n"
        f"  • W1 ({sprint['assignments']['worker_1']['role']}): Tamamlandı\n"
        f"  • W2 ({sprint['assignments']['worker_2']['role']}): Tamamlandı\n"
        f"  • W3 ({sprint['assignments']['worker_3']['role']}): Tamamlandı\n\n"
        f"🔄 Review döngüsü: {sprint['review_cycles']}\n"
        f"⏱ Süre: {sprint['duration']}"
    )

def format_error_alert(error: dict) -> str:
    return (
        f"🚨 *Hata Oluştu*\n\n"
        f"Sprint: {error.get('sprint_id', 'N/A')}\n"
        f"Hata: {error['message']}\n"
        f"Aksiyon: {error.get('action', 'Manuel müdahale gerekebilir')}"
    )
```

---

## Güvenlik

- Tüm komutlar `TELEGRAM_CHAT_ID` kontrolünden geçer
- Yetkisiz chat'ten gelen mesajlar sessizce görmezden gelinir
- Bot token `.env`'den okunur, hardcode edilmez
- Callback data imzalanmaz ama flow_id UUID olduğundan güvenli

---

## References

- `project-architecture/SKILL.md` — EventBus event isimleri
- `python-async-patterns/SKILL.md` — async yapı kuralları