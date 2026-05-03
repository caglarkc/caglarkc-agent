---
name: database-schema-review
description: Planner AI için — SQLite tablo tasarımını, Pydantic storage modellerini ve repository metodlarının doğruluğunu review sırasında doğrulamak.
---

## Purpose

DB şemasının proje ihtiyaçlarına uygun tasarlandığını garantiler.
Eksik index, yanlış tip, güvensiz sorgu gibi sorunları yakalar.
Repository metodlarının Pydantic modelleriyle uyumluluğunu kontrol eder.

---

## When to Apply

- `src/storage/models.py` veya `src/storage/repository.py` review edilirken
- Yeni tablo veya alan eklenirken
- Migration planlanırken

---

## Rules

- Primary key her tabloda `TEXT` (UUID string), otomatik artan INT kullanılmaz.
- `created_at` ve `updated_at` her tabloda zorunlu.
- JSON veriler `TEXT` olarak saklanır, `json.dumps/loads` ile.
- Foreign key `PRAGMA foreign_keys=ON` ile aktif edilmeli.
- Tüm sorgular parameterized (`?` placeholder), string concatenation yasak.
- `aiosqlite` kullanımı zorunlu, `sqlite3` direkt kullanım yasak.
- Index: sık sorgulanan alanlar (project_id, status, created_at) için.

---

## Guidelines

Schema kontrol:
```sql
-- DOĞRU tablo yapısı
CREATE TABLE IF NOT EXISTS file_records (
    file_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    sprint_id TEXT REFERENCES sprints(sprint_id),
    path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    worker_id TEXT,
    attempt_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_file_records_project_id ON file_records(project_id);
CREATE INDEX IF NOT EXISTS idx_file_records_status ON file_records(status);
```

Repository metod kontrol:
```python
# DOĞRU — parametrize sorgu
async def get_file_record(self, file_id: str) -> FileRecord | None:
    async with aiosqlite.connect(self.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM file_records WHERE file_id = ?", (file_id,)
        )
        row = await cursor.fetchone()
        return FileRecord(**dict(row)) if row else None

# YANLIŞ — string concatenation (SQL injection)
await conn.execute(f"SELECT * FROM file_records WHERE file_id = '{file_id}'")
```

---

## References

- `aiosqlite-patterns-skill/SKILL.md` — aiosqlite kullanımı
- `pydantic-v2-model-definition-skill/SKILL.md` — model tanımları
- `sql-injection-review-skill/SKILL.md` — güvenli sorgular
