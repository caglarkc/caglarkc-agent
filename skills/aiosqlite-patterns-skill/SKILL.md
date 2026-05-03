---
name: aiosqlite-patterns
description: Coder AI için — aiosqlite ile async SQLite operasyonlarının bu projedeki standart pattern'ları; connection, query, transaction ve row factory.
---

## Purpose

`src/storage/repository.py`'deki tüm DB operasyonlarının tutarlı yazılmasını sağlar.
Row factory, parameterized query ve async context manager kullanımını standartlaştırır.
SQLite concurrent write kısıtını göz önünde bulundurarak güvenli operasyonlar sağlar.

---

## When to Apply

- `src/storage/repository.py`'e yeni metod eklenirken
- Yeni tablo veya sorgu yazılırken
- DB'den model nesnesi okuma/yazma yapılırken

---

## Rules

- Her operasyon `async with aiosqlite.connect(self.db_path) as conn:` içinde.
- Row factory: `conn.row_factory = aiosqlite.Row` — dict benzeri erişim.
- Tüm sorgular parameterized: `?` placeholder.
- Write sonrası `await conn.commit()`.
- `fetchone()` → `None` kontrolü zorunlu.
- `fetchall()` → boş list döner, `None` değil.

---

## Guidelines

CRUD şablonları:
```python
# CREATE / UPSERT
async def upsert_file_record(self, record: FileRecord) -> None:
    async with aiosqlite.connect(self.db_path) as conn:
        await conn.execute(
            """INSERT OR REPLACE INTO file_records
               (file_id, project_id, path, status, worker_id, attempt_count,
                last_error, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.file_id, record.project_id, record.path,
             record.status, record.worker_id, record.attempt_count,
             record.last_error, record.created_at.isoformat(),
             record.updated_at.isoformat())
        )
        await conn.commit()

# READ ONE
async def get_file_record(self, file_id: str) -> FileRecord | None:
    async with aiosqlite.connect(self.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM file_records WHERE file_id = ?",
            (file_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return FileRecord.from_db_row(dict(row))

# READ MANY
async def list_file_records(self, project_id: str) -> list[FileRecord]:
    async with aiosqlite.connect(self.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM file_records WHERE project_id = ? ORDER BY created_at",
            (project_id,)
        )
        rows = await cursor.fetchall()
        return [FileRecord.from_db_row(dict(row)) for row in rows]

# UPDATE
async def update_file_status(self, file_id: str, status: str) -> None:
    async with aiosqlite.connect(self.db_path) as conn:
        await conn.execute(
            "UPDATE file_records SET status = ?, updated_at = ? WHERE file_id = ?",
            (status, datetime.utcnow().isoformat(), file_id)
        )
        await conn.commit()
```

---

## References

- `database-schema-review-skill/SKILL.md` — şema tasarımı
- `async-transaction-management-skill/SKILL.md` — transaction
- `pydantic-v2-model-definition-skill/SKILL.md` — model from_db_row
