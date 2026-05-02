---
name: db-connection-pool
description: Coder AI için — SQLite veya PostgreSQL için async bağlantı havuzu oluşturmak; her sorgu için yeni bağlantı açmamak.
---

## Purpose

Her DB sorgusunda yeni bağlantı açmak yavaş ve kaynak israfıdır.
Connection pool: bağlantıları önceden oluşturur, sorgu sonrası geri alır.
aiosqlite ve asyncpg için pool stratejileri farklıdır.

---

## When to Apply

- DB sorgularının sık yapıldığı bileşenlerde
- Worker'lar paralel DB erişimi yaparken
- Sprint state SQLite'a yazılırken

---

## Rules

- SQLite: aiosqlite + asyncio.Lock (tek yazıcı).
- PostgreSQL: asyncpg pool (built-in).
- Pool boyutu: CPU sayısı × 2 (varsayılan).
- Bağlantı zaman aşımı: 5 saniye.

---

## Guidelines

```python
import asyncio
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncIterator

class SQLitePool:
    """SQLite için thread-safe async pool simülasyonu."""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self._path = db_path
        self._pool: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue(maxsize=pool_size)
        self._size = pool_size
        self._initialized = False
    
    async def initialize(self) -> None:
        for _ in range(self._size):
            conn = await aiosqlite.connect(self._path)
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await self._pool.put(conn)
        self._initialized = True
    
    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[aiosqlite.Connection]:
        conn = await asyncio.wait_for(self._pool.get(), timeout=5.0)
        try:
            yield conn
        finally:
            await self._pool.put(conn)
    
    async def close(self) -> None:
        while not self._pool.empty():
            conn = self._pool.get_nowait()
            await conn.close()

# asyncpg için pool (PostgreSQL)
async def create_pg_pool(dsn: str):
    import asyncpg
    return await asyncpg.create_pool(
        dsn,
        min_size=2,
        max_size=10,
        command_timeout=10.0,
    )

# Kullanım
_pool: SQLitePool | None = None

async def get_pool(db_path: str) -> SQLitePool:
    global _pool
    if _pool is None:
        _pool = SQLitePool(db_path)
        await _pool.initialize()
    return _pool
```

---

## References

- `db-query-with-timeout-skill/SKILL.md` — DB sorgu timeout
- `async-context-manager-skill/SKILL.md` — async context manager
- `settings-validation-skill/SKILL.md` — ayar doğrulama
