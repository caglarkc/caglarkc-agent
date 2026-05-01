---
name: upsert-pattern
description: Coder AI için — SQLite'ta "var ise güncelle, yok ise ekle" operasyonunun doğru yolu; INSERT OR REPLACE ve ON CONFLICT DO UPDATE kullanımı.
---

## Purpose

Duplicate key hatasından kaçınarak idempotent yazma operasyonu sağlar.
Daemon restart sonrasında aynı kayıt tekrar yazılırsa hata oluşmaz.
`project_id`, `file_id` gibi primary key'li tablolarda güvenli yazma sağlar.

---

## When to Apply

- Proje, sprint veya dosya kaydı oluşturulurken/güncellenirken
- Daemon recovery sonrası state yeniden yazılırken
- `create_or_update` semantiği gereken her yerde

---

## Rules

- Basit upsert: `INSERT OR REPLACE INTO ...` — tüm satırı yazar.
- Kısmi güncelleme: `INSERT INTO ... ON CONFLICT(id) DO UPDATE SET ...`.
- `INSERT OR REPLACE` primary key dışındaki alanları sıfırlayabilir — dikkat.
- `created_at` korunması gerekiyorsa `ON CONFLICT DO UPDATE` kullanılır.
- Upsert sonrası her zaman `await conn.commit()`.

---

## Guidelines

Basit upsert (tüm alanlar güncel):
```python
async def upsert_project(self, project: Project) -> None:
    async with aiosqlite.connect(self.db_path) as conn:
        await conn.execute(
            """INSERT OR REPLACE INTO projects
               (project_id, name, description, status, created_at, updated_at, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (project.project_id, project.name, project.description,
             project.status, project.created_at.isoformat(),
             project.updated_at.isoformat(),
             json.dumps(project.metadata))
        )
        await conn.commit()
```

Kısmi upsert (created_at korunur):
```python
async def upsert_file_record(self, record: FileRecord) -> None:
    async with aiosqlite.connect(self.db_path) as conn:
        await conn.execute(
            """INSERT INTO file_records
               (file_id, project_id, path, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(file_id) DO UPDATE SET
               status = excluded.status,
               updated_at = excluded.updated_at
               WHERE file_records.status != 'done'""",
            (record.file_id, record.project_id, record.path,
             record.status, record.created_at.isoformat(),
             record.updated_at.isoformat())
        )
        await conn.commit()
```

---

## References

- `aiosqlite-patterns-skill/SKILL.md` — genel DB pattern'ları
- `async-transaction-management-skill/SKILL.md` — transaction
- `idempotency-enforcement-skill/SKILL.md` — idempotent operasyonlar
