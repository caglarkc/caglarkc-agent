---
name: sprint-auto-continuation
description: Planner AI için — tamamlanan sprintten sonra kullanıcı müdahalesi olmadan bir sonraki sprintin otomatik başlatılması.
---

## Purpose

Her sprint sonunda kullanıcıdan "devam et" beklemek verimliliği düşürür.
Auto-continuation: sprint backlog varsa ve kullanıcı izin vermişse otomatik başlar.
"Sessiz mod" ile insan müdahalesi minimuma iner.

---

## When to Apply

- Kullanıcı "otomatik devam et" modunu açtığında
- Backlog'da bekleyen görevler varken sprint bittiğinde
- CI/CD benzeri otomasyon pipeline'ında

---

## Rules

- Auto-continuation: kullanıcı açıkça onaylamadan etkinleşmez.
- Backlog boşsa durur, kullanıcıya bildirir.
- Her otomatik başlatmada kullanıcı bilgilendirilir (bildirim).
- Hata sonrası: otomatik devam etmez, kullanıcı uyarılır.

---

## Guidelines

```python
def should_auto_continue(state: dict) -> bool:
    if not state.get("auto_continue_enabled"):
        return False
    if state.get("sprint_status") != "completed":
        return False
    if state.get("last_sprint_had_errors"):
        return False
    backlog = state.get("backlog", [])
    return len(backlog) > 0

async def auto_continue_node(state: dict) -> dict:
    if not should_auto_continue(state):
        return {"waiting_for_user": True}
    
    backlog = state.get("backlog", [])
    next_goal = backlog[0]
    
    # Bildirim gönder
    await notify_user_auto_start(next_goal, state)
    
    return {
        "sprint_goal":   next_goal,
        "sprint_status": "planning",
        "backlog":       backlog[1:],
        "auto_started":  True,
    }

async def notify_user_auto_start(goal: str, state: dict) -> None:
    msg = (
        f"[Otomatik] Yeni sprint başlatılıyor:\n"
        f"Hedef: {goal}\n"
        f"Durdurmak için: /sprint stop"
    )
    # EventBus veya Telegram üzerinden bildirim
    event_bus = state.get("event_bus")
    if event_bus:
        await event_bus.publish("user.notification", {"message": msg})
```

---

## References

- `sprint-restart-skill/SKILL.md` — sprint yeniden başlatma
- `sprint-pause-resume-skill/SKILL.md` — sprint duraklama/devam
- `approval-flow-orchestration-skill/SKILL.md` — onay akışı
