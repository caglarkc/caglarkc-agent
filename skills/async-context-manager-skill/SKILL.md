---
name: async-context-manager
description: Coder AI için — async with bloğu gerektiren kaynakların (DB bağlantısı, HTTP session, kilit) doğru açılıp kapatılması için async context manager yazmak.
---

## Purpose

DB bağlantısı veya HTTP session `async with` olmadan kullanılırsa leak olur.
`__aenter__` / `__aexit__` pattern, kaynakların garantili kapatılmasını sağlar.
Exception olsa bile `finally` bloğu kaynağı kapatır.

---

## When to Apply

- `aiosqlite.connect()` kullanımında
- `aiohttp.ClientSession` yönetiminde
- `asyncio.Lock` veya `asyncio.Semaphore` ile kritik bölge korurken
- Kendi kaynak sınıfı yazılırken

---

## Rules

- DB bağlantısı: her işlem için ayrı `async with aiosqlite.connect()` bloğu.
- HTTP session: uygulama yaşam süresi boyunca tek session (startup/shutdown).
- Semaphore: maksimum eşzamanlı worker sayısını sınırlamak için.
- `contextlib.asynccontextmanager` dekoratörü basit use-case için yeterli.

---

## Guidelines

```python
import asyncio
import aiosqlite
from contextlib import asynccontextmanager

# Basit async context manager
@asynccontextmanager
async def get_db_connection(db_path: str):
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn

# Kullanım
async def fetch_project(project_id: str) -> dict | None:
    async with get_db_connection(settings.db_path) as conn:
        cursor = await conn.execute(
            "SELECT * FROM projects WHERE project_id = ?",
            (project_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

# Sınıf tabanlı async context manager
class WorkerSemaphore:
    def __init__(self, max_workers: int):
        self._sem = asyncio.Semaphore(max_workers)
    
    async def __aenter__(self):
        await self._sem.acquire()
        return self
    
    async def __aexit__(self, *args):
        self._sem.release()

# Kullanım
worker_sem = WorkerSemaphore(max_workers=3)

async def run_worker(task):
    async with worker_sem:
        await execute_task(task)
```

---

## References

- `aiosqlite-patterns-skill/SKILL.md` — DB işlemleri
- `async-function-template-skill/SKILL.md` — async template
- `worker-status-tracking-skill/SKILL.md` — worker yönetimi
