---
name: context-manager-implementation
description: Coder AI için — async context manager (async with) ve sync context manager (__enter__/__exit__) implementasyonunun bu projede doğru kullanımı.
---

## Purpose

Kaynakların doğru açılıp kapatılmasını sağlar.
`contextlib.asynccontextmanager` ile dekoratör tabanlı context manager yazmayı sağlar.
LangGraph graph runtime, DB connection, HTTP client için standart pattern'ı uygular.

---

## When to Apply

- Açılıp kapatılması gereken kaynak (DB, HTTP, lock, graph) yönetilirken
- `graph_runtime()` gibi lifecycle context manager yazılırken
- Test setup/teardown yönetilirken

---

## Rules

- DB ve HTTP kaynakları her zaman `async with` ile kullanılır.
- Kendi sınıfı için context manager: `__aenter__` ve `__aexit__` implementasyonu.
- Dekoratör tabanlı: `@asynccontextmanager` ile `yield` kullanımı.
- `__aexit__`'te exception suppress edilmez — `return False` veya `return None`.
- `finally` bloğu cleanup için zorunlu (exception durumunda da çalışır).

---

## Guidelines

Dekoratör tabanlı async context manager:
```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator


@asynccontextmanager
async def graph_runtime() -> AsyncGenerator[CompiledGraph, None]:
    """LangGraph runtime lifecycle yönetimi."""
    async with AsyncSqliteSaver.from_conn_string(
        settings.graph_checkpoint_path
    ) as checkpointer:
        graph = build_graph().compile(checkpointer=checkpointer)
        try:
            yield graph
        finally:
            logger.info("Graph runtime kapatıldı")
```

Sınıf tabanlı async context manager:
```python
class DatabaseRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None
    
    async def __aenter__(self) -> "DatabaseRepository":
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._initialize_schema()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._conn:
            await self._conn.close()
        return None  # exception suppress edilmez
```

Kullanım:
```python
# graph runtime
async with graph_runtime() as graph:
    await graph.ainvoke(state, config=config)

# repository
async with DatabaseRepository(db_path) as repo:
    record = await repo.get_file_record(file_id)
```

---

## References

- `resource-cleanup-review-skill/SKILL.md` — kaynak temizliği
- `asyncio-lock-usage-skill/SKILL.md` — lock context manager
- `checkpoint-strategy-review-skill/SKILL.md` — graph runtime
