---
name: resource-cleanup-review
description: Planner AI için — DB connection, HTTP client, dosya handle, asyncio task gibi kaynakların düzgün kapatıldığını ve sızdırılmadığını review sırasında kontrol etmek.
---

## Purpose

Resource leak'leri review sırasında yakalar.
Kapatılmayan DB connection zamanla connection pool'u tüketir.
Temizlenmeyen asyncio task'lar memory leak yaratır.

---

## When to Apply

- DB, HTTP, dosya, lock, subprocess gibi kaynak kullanan kod review edilirken
- `async with` veya `try/finally` bloğu içeren kod review edilirken
- Long-running daemon kodu review edilirken

---

## Rules

- DB connection: her zaman `async with aiosqlite.connect(...)` ile kullanılır.
- HTTP client: her zaman `async with httpx.AsyncClient()` ile kullanılır.
- Dosya: her zaman `async with aiofiles.open(...)` ile kullanılır.
- asyncio Task: `asyncio.create_task()` sonrası iptal edilmeden abandon edilmez.
- Lock: `async with self._lock` ile kullanılır, manuel `acquire/release` yerine.
- `finally` bloğu connection kapatma için kullanılır (exception durumunda da).

---

## Guidelines

Context manager zorunlu kaynaklar:
```python
# DB — DOĞRU
async with aiosqlite.connect(self.db_path) as conn:
    await conn.execute(query, params)
    await conn.commit()
# Blok bittikten sonra conn otomatik kapanır

# DB — YANLIŞ (leak riski)
conn = await aiosqlite.connect(self.db_path)
await conn.execute(query)
# conn.close() unutulursa leak!

# HTTP — DOĞRU
async with httpx.AsyncClient(timeout=30) as client:
    response = await client.post(url, json=data)

# Dosya — DOĞRU
async with aiofiles.open(file_path, "w") as f:
    await f.write(content)
```

Task cleanup:
```python
# DOĞRU — task referansı tutulur ve graceful shutdown'da iptal edilir
class MyService:
    def __init__(self):
        self._tasks: set[asyncio.Task] = set()
    
    def start_task(self, coro):
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
    
    async def shutdown(self):
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
```

---

## References

- `async-context-manager-skill/SKILL.md` — context manager pattern
- `graceful-shutdown-implementation-skill/SKILL.md` — shutdown
- `asyncio-lock-usage-skill/SKILL.md` — lock kullanımı
