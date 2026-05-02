---
name: migration-strategy
description: Planner AI için — mevcut DB şemasına yeni sütun veya tablo eklenirken migration stratejisini planlamak; veri kaybını önlemek.
---

## Purpose

Şema değişikliği production'daki mevcut veriyi bozabilir.
Migration adımları önceden planlanırsa güvenli geçiş yapılır.
Bu projede aiosqlite kullanılıyor — migration SQL dosyaları ile yapılır.

---

## When to Apply

- Mevcut tabloya yeni sütun eklenirken
- Yeni tablo oluşturulurken
- Sütun tipi veya kısıtı değiştirilirken
- Schema versiyonu artırılırken

---

## Rules

- Migration geri alınamaz — `decisions` tablosuna kayıt düşülür.
- Yeni sütun: `DEFAULT` değeriyle eklenir — NULL değilse.
- Mevcut veriye zarar vermeden migration yapılır.
- Migration versiyonu `schema_versions` tablosunda takip edilir.
- Test ortamında migration önce çalıştırılır.

---

## Guidelines

```python
# src/storage/migrations.py
MIGRATIONS = {
    "001_initial": """
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL
        );
    """,
    "002_add_sprint_goal": """
        ALTER TABLE sprints ADD COLUMN goal TEXT DEFAULT '';
    """,
    "003_add_decisions": """
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            sprint_id TEXT,
            summary TEXT NOT NULL,
            rationale TEXT NOT NULL,
            decision_type TEXT DEFAULT 'general',
            created_at TEXT NOT NULL
        );
    """,
}

async def run_migrations(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as conn:
        # Versiyon tablosu oluştur
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)
        
        cursor = await conn.execute("SELECT version FROM schema_versions")
        applied = {row[0] for row in await cursor.fetchall()}
        
        for version, sql in sorted(MIGRATIONS.items()):
            if version not in applied:
                await conn.executescript(sql)
                await conn.execute(
                    "INSERT INTO schema_versions VALUES (?, ?)",
                    (version, datetime.utcnow().isoformat())
                )
                logger.info(f"Migration uygulandı: {version}")
        
        await conn.commit()
```

---

## References

- `aiosqlite-patterns-skill/SKILL.md` — DB operasyonları
- `architecture-decision-record-skill/SKILL.md` — ADR kaydı
- `upsert-pattern-skill/SKILL.md` — upsert pattern
