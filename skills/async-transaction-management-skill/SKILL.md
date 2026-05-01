---
name: async-transaction-management
description: Coder AI için — aiosqlite ile çoklu yazma operasyonunu tek atomik transaction içinde yönetme; commit ve rollback pattern'ları.
---

## Purpose

Birden fazla DB yazmasının ya hepsinin başarılı ya da hiçbirinin gerçekleşmemesini garantiler.
Sprint oluşturma + dosya kayıtları gibi bağlı operasyonlar atomik olmalıdır.
Transaction dışında kalan yazmaları tespit eder ve düzeltir.

---

## When to Apply

- Birden fazla tabloya bağımlı yazma yapılırken
- Sprint oluşturma (sprint + file_records) gibi atomik işlemlerde
- Kısmi başarısızlığın tutarsızlığa yol açacağı durumlarda

---

## Rules

- `async with aiosqlite.connect(...) as conn:` tek connection ile tüm işlemler.
- Birden fazla yazma: tek `commit()` en sonda.
- Hata durumunda `conn.rollback()` çağrılır (context manager otomatik yapar).
- Transaction içinde başka async IO (LLM çağrısı gibi) yasak — connection açık kalır.
- SQLite concurrent write yasak — transaction sırasında lock tutar.

---

## Guidelines

Atomik sprint oluşturma:
```python
async def create_sprint_with_files(
    self,
    sprint: Sprint,
    file_records: list[FileRecord]
) -> None:
    async with aiosqlite.connect(self.db_path) as conn:
        try:
            # Sprint oluştur
            await conn.execute(
                """INSERT INTO sprints (sprint_id, project_id, number, status, started_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (sprint.sprint_id, sprint.project_id, sprint.number,
                 sprint.status, sprint.started_at.isoformat())
            )
            
            # Dosya kayıtlarını oluştur
            for record in file_records:
                await conn.execute(
                    """INSERT INTO file_records (file_id, project_id, sprint_id, path, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (record.file_id, record.project_id, sprint.sprint_id,
                     record.path, record.status)
                )
            
            # Tek seferde commit — atomik
            await conn.commit()
            logger.info(f"Sprint {sprint.sprint_id} ve {len(file_records)} dosya oluşturuldu")
        
        except Exception as e:
            await conn.rollback()
            logger.error(f"Sprint oluşturma başarısız, rollback yapıldı: {e}")
            raise
```

---

## References

- `aiosqlite-patterns-skill/SKILL.md` — temel DB pattern'ları
- `upsert-pattern-skill/SKILL.md` — upsert
- `concurrency-safety-review-skill/SKILL.md` — concurrent yazma
