---
name: asyncio-lock-usage
description: Coder AI için — shared state'i korumak için asyncio.Lock() kullanımının doğru yolu; StateManager, file_registry ve diğer paylaşılan kaynaklarda race condition önleme.
---

## Purpose

Shared state'e eş zamanlı erişimde data corruption'ı önler.
`asyncio.Lock()` event loop bloklamadan mutual exclusion sağlar.
`threading.Lock()` değil `asyncio.Lock()` — async context'te threading lock kullanılamaz.

---

## When to Apply

- Birden fazla coroutine'in aynı dict/list'e yazma yapabileceği durumlarda
- Singleton nesne state'i güncellenirken (StateManager, EventBus history)
- File reservation (check-then-set) operasyonlarında

---

## Rules

- `asyncio.Lock()` always `async with` ile kullanılır — manuel `acquire/release` yasak.
- Lock'lar mümkün olan en kısa süre tutulur (IO içinde lock tutma).
- Singleton'larda lock instance variable olarak tutulur.
- Deadlock: A lock'u tutarken B'yi bekleyip B de A'yı bekliyorsa → önle.
- `threading.Lock()` async context'te kullanılmaz.

---

## Guidelines

Temel lock kullanımı:
```python
class StateManager:
    def __init__(self):
        self._state: dict[str, dict] = {}
        self._lock = asyncio.Lock()
    
    async def update(self, project_id: str, updates: dict) -> None:
        async with self._lock:
            current = self._state.get(project_id, {})
            current.update(updates)
            self._state[project_id] = current
    
    async def get(self, project_id: str) -> dict:
        async with self._lock:
            return dict(self._state.get(project_id, {}))
```

Atomic check-and-set (file reservation):
```python
class FileRegistry:
    def __init__(self):
        self._registry: dict[str, str] = {}
        self._lock = asyncio.Lock()
    
    async def reserve(self, file_path: str, worker_id: str) -> bool:
        async with self._lock:
            if self._registry.get(file_path) == "planned":
                self._registry[file_path] = "reserved"
                return True
            return False  # başka worker aldı
```

IO içinde lock TUTMA (yanlış pattern):
```python
# YANLIŞ — lock tutarken IO yapılıyor, event loop bloklanıyor
async with self._lock:
    data = await external_api.fetch()  # lock tutulurken IO!
    self._state.update(data)

# DOĞRU — IO dışarıda, sadece state güncelleme lock içinde
data = await external_api.fetch()  # lock dışı
async with self._lock:
    self._state.update(data)  # sadece in-memory güncelleme
```

---

## References

- `concurrency-safety-review-skill/SKILL.md` — concurrency review
- `file-reservation-pattern-skill/SKILL.md` — dosya rezervasyon
- `asyncio-task-creation-skill/SKILL.md` — task yönetimi
