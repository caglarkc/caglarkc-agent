---
name: heartbeat-emission
description: Coder AI için — stall detection için dispatcher ve worker node'larından düzenli heartbeat event'i emit etmek.
---

## Purpose

Sistemin canlı olduğunu stall detection mekanizmasına bildirmek için heartbeat'i düzenli emit eder.
600 saniye boyunca heartbeat gelmazsa `system.stalled` tetiklenir.
Worker başlamadan ve bittikten sonra heartbeat gönderilir.

---

## When to Apply

- Dispatcher node'da görev atanırken
- Worker node'da dosya üretimi başlarken ve biterken
- Background monitoring loop'unda

---

## Rules

- Heartbeat event: `system.heartbeat`.
- Payload zorunlu alanlar: `project_id`, `timestamp`.
- Opsiyonel: `worker_id`, `task`, `node`.
- Exception heartbeat'i engellemez — try/except içinde emit edilir.
- Çok sık heartbeat: her worker görevi başında ve sonunda yeterli.

---

## Guidelines

Node içinde heartbeat:
```python
# dispatcher.py — görev atandıktan sonra
await event_bus.emit("system.heartbeat", {
    "project_id": state.get("project_id"),
    "node": "dispatcher",
    "worker_id": assigned_worker_id,
    "task": target_file,
    "timestamp": datetime.utcnow().isoformat()
})

# worker.py — dosya üretimi başlamadan önce
await event_bus.emit("system.heartbeat", {
    "project_id": state.get("project_id"),
    "node": "worker",
    "worker_id": worker_id,
    "task": target_file,
    "status": "started",
    "timestamp": datetime.utcnow().isoformat()
})

# worker.py — dosya yazıldıktan sonra
await event_bus.emit("system.heartbeat", {
    "project_id": state.get("project_id"),
    "node": "worker",
    "worker_id": worker_id,
    "task": target_file,
    "status": "completed",
    "timestamp": datetime.utcnow().isoformat()
})
```

Background heartbeat (daemon):
```python
async def _heartbeat_loop(self):
    while True:
        try:
            active_projects = await graph_manager.get_active_projects()
            for project_id in active_projects:
                await event_bus.emit("system.heartbeat", {
                    "project_id": project_id,
                    "source": "daemon_monitor",
                    "timestamp": datetime.utcnow().isoformat()
                })
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Heartbeat hatası: {e}")
        await asyncio.sleep(30)
```

---

## References

- `stall-detection-response-skill/SKILL.md` — stall tespiti
- `event-emission-pattern-skill/SKILL.md` — event emit
- `asyncio-task-creation-skill/SKILL.md` — background task
