---
name: code-singleton-pattern
description: Coder AI için — Python Singleton desenini doğru uygulamak; EventBus, config, DB pool gibi paylaşılan kaynaklar için tek örnek garantisi.
---

## Purpose

EventBus veya DB pool her yerde aynı örnek olmalı.
Singleton: sınıfın yalnızca bir örneği oluşturulur.
Thread-safe ve async-safe implementasyon önemlidir.

---

## When to Apply

- Global shared state gerektiğinde (EventBus, MetricsCollector)
- Kaynak açma maliyetli olduğunda (DB bağlantı havuzu)
- Konfigürasyon yöneticisi için

---

## Rules

- `__new__` tabanlı: thread-safe değil, basit kullanım için.
- Module-level instance: Python'un en Pythonik singleton'ı.
- Lock ile: thread-safe gerektiğinde.
- Test: reset mekanizması her zaman var.

---

## Guidelines

```python
import asyncio
from threading import Lock

# 1. Module-level singleton (Pythonik, önerilen)
class _EventBus:
    def __init__(self):
        self._handlers = {}

    async def publish(self, event: str, payload: dict) -> None:
        for handler in self._handlers.get(event, []):
            await handler(payload)

    def subscribe(self, event: str, handler) -> None:
        self._handlers.setdefault(event, []).append(handler)

_event_bus_instance: _EventBus | None = None

def get_event_bus() -> _EventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = _EventBus()
    return _event_bus_instance

def reset_event_bus() -> None:
    global _event_bus_instance
    _event_bus_instance = None

# 2. Thread-safe singleton
class ThreadSafeSingleton:
    _instance = None
    _lock: Lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

# 3. Async singleton (ilk çağrıda init)
class AsyncSingleton:
    _instance = None
    _init_lock: asyncio.Lock | None = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            if cls._init_lock is None:
                cls._init_lock = asyncio.Lock()
            async with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._async_init()
        return cls._instance

    async def _async_init(self) -> None:
        pass
```

---

## References

- `dependency-injection-patterns-skill/SKILL.md` — bağımlılık enjeksiyonu
- `async-event-driven-skill/SKILL.md` — async event driven
- `db-connection-pool-skill/SKILL.md` — DB bağlantı havuzu
