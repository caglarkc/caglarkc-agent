---
name: code-context-manager-advanced
description: Coder AI için — contextlib ile özel context manager yazmak; kaynakları otomatik serbest bırakmak ve cleanup garantilemek.
---

## Purpose

`try/finally` tekrar eden cleanup kodu şişirir.
Context manager: `with` bloğu çıkınca her zaman cleanup çalışır.
Async version: `async with` ile DB transaction, lock, dosya handle yönetimi.

---

## When to Apply

- Kaynak açma/kapama zorunlu olduğunda (DB bağlantısı, dosya, lock)
- Cleanup garantisi gereken işlemlerde
- Geçici state değişikliği sonrası geri almak için

---

## Rules

- `contextlib.contextmanager`: sync generator tabanlı.
- `contextlib.asynccontextmanager`: async generator tabanlı.
- `__enter__`/`__exit__`: sınıf tabanlı.
- Hata: `__exit__` True döndürürse bastırılır — dikkatli kullan.

---

## Guidelines

```python
from contextlib import contextmanager, asynccontextmanager
import asyncio

@contextmanager
def temporary_state_change(state: dict, **overrides):
    original = {k: state.get(k) for k in overrides}
    state.update(overrides)
    try:
        yield state
    finally:
        state.update({k: v for k, v in original.items() if v is not None})
        for k in overrides:
            if original.get(k) is None and k in state:
                del state[k]

@asynccontextmanager
async def managed_sprint(state: dict, event_bus):
    await event_bus.publish("sprint.started", {"sprint_id": state["sprint_id"]})
    try:
        yield state
        await event_bus.publish("sprint.completed", {"sprint_id": state["sprint_id"]})
    except Exception as exc:
        await event_bus.publish("sprint.failed", {
            "sprint_id": state["sprint_id"],
            "error": str(exc),
        })
        raise

# Sınıf tabanlı context manager
class FileLock:
    def __init__(self, path: str):
        self._path = path + ".lock"
        self._file = None

    def __enter__(self):
        from pathlib import Path
        p = Path(self._path)
        if p.exists():
            raise IOError(f"Dosya kilitli: {self._path}")
        p.touch()
        return self

    def __exit__(self, *_):
        from pathlib import Path
        Path(self._path).unlink(missing_ok=True)
        return False

# Kullanım
with temporary_state_change(state, sprint_status="dry_run"):
    result = simulate_sprint(state)
```

---

## References

- `async-context-manager-skill/SKILL.md` — async context manager
- `file-write-atomicity-skill/SKILL.md` — atomik dosya yazma
- `async-lock-usage-skill/SKILL.md` — async kilit
