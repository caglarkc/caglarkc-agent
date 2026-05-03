---
name: concurrency-safety-review
description: Planner AI için — eş zamanlı async operasyonlarda race condition, shared state mutasyonu ve lock eksikliği gibi concurrency güvenlik sorunlarını review sırasında tespit etmek.
---

## Purpose

Birden fazla coroutine'in aynı anda aynı kaynağa eriştiği durumları tespit eder.
Race condition ve veri tutarsızlığına yol açabilecek kod bölümlerini işaretler.
Gerektiğinde `asyncio.Lock` kullanımını zorunlu kılar.

---

## When to Apply

- Birden fazla worker aynı anda çalışabilecekse
- Singleton nesneye (EventBus, StateManager) eş zamanlı yazma varsa
- Paylaşılan veri yapısı (dict, list) async context'te modifiye ediliyorsa
- File I/O birden fazla coroutine'den yapılıyorsa

---

## Rules

- `StateManager` state güncellemeleri `asyncio.Lock` ile korunmalı.
- `file_registry` güncellemeleri atomic olmalı (reservation + write sıralı).
- Worker'lar aynı dosyaya eş zamanlı yazamaz — `file_registry` reservation bunu engeller.
- EventBus emit thread-safe olmalı (exception catch ile).
- `asyncio.gather()` ile paralel çalışan coroutine'ler aynı dict'i mutate etmemeli.

---

## Guidelines

Race condition tespiti:
```python
# YANLIŞ — race condition
class StateManager:
    _state: dict = {}
    
    async def update(self, project_id: str, data: dict):
        current = self._state.get(project_id, {})
        current.update(data)  # başka coroutine aynı anda burada olabilir
        self._state[project_id] = current

# DOĞRU — lock ile korunmuş
class StateManager:
    _state: dict = {}
    _lock: asyncio.Lock = asyncio.Lock()
    
    async def update(self, project_id: str, data: dict):
        async with self._lock:
            current = self._state.get(project_id, {})
            current.update(data)
            self._state[project_id] = current
```

File reservation race condition:
```python
# YANLIŞ — check-then-act race condition
if file_registry[path] == "planned":
    file_registry[path] = "reserved"  # iki worker aynı anda geçebilir

# DOĞRU — atomic check-and-set (lock içinde)
async with self._lock:
    if file_registry.get(path) == "planned":
        file_registry[path] = "reserved"
        return True
    return False  # başka worker aldı
```

`asyncio.gather()` güvenli kullanım:
```python
# DOĞRU — her coroutine kendi sonucunu döndürür, paylaşılan state yok
results = await asyncio.gather(
    worker_a.execute(task_a),
    worker_b.execute(task_b),
    return_exceptions=True
)
```

---

## References

- `asyncio-lock-usage-skill/SKILL.md` — lock kullanımı
- `file-reservation-pattern-skill/SKILL.md` — dosya rezervasyonu
- `async-architecture-validation-skill/SKILL.md` — async doğrulama
