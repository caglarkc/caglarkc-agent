---
name: idempotency-enforcement
description: Coder AI için — aynı operasyonun birden fazla kez çalıştırılmasının güvenli olduğunu garanti etmek; tekrarlanan daemon restart ve LangGraph resume senaryolarında veri tutarlılığını korumak.
---

## Purpose

Daemon restart veya graph resume sonrasında aynı işlemin iki kez yapılmasını önler.
"En az bir kez çalışır" garantisi yerine "tam bir kez çalışır" etkisini sağlar.
`INSERT OR REPLACE`, approval idempotency ve duplicate event korumasını kapsar.

---

## When to Apply

- Daemon restart sonrası recovery kodu yazılırken
- Approval guard implementasyonu yapılırken
- Yeni Sprint veya FileRecord oluşturulurken
- Event handler'ı tekrarlanan event'e karşı korurken

---

## Rules

- DB yazma: `INSERT OR REPLACE` veya `ON CONFLICT DO NOTHING`.
- Approval: `approval_id` ile duplicate approval tespiti.
- Sprint oluşturma: `sprint_id` zaten varsa güncelleme yap, yeniden ekleme yapma.
- Event handler: işlendi mi kontrolü `processed_events` set ile.
- File yazma: dosya zaten `done` ise yeniden yazma.

---

## Guidelines

DB idempotency:
```python
# Dosya zaten done ise güncelleme — durumu geri götürme
async def upsert_file_record(self, record: FileRecord) -> None:
    async with aiosqlite.connect(self.db_path) as conn:
        await conn.execute("""
            INSERT INTO file_records (file_id, project_id, path, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_id) DO UPDATE SET
                status = excluded.status,
                updated_at = excluded.updated_at
            WHERE file_records.status NOT IN ('done')
        """, (...))
        await conn.commit()
```

Approval idempotency:
```python
class ApprovalGuard:
    _processed_approvals: set[str] = set()
    _lock = asyncio.Lock()
    
    async def process_approval(self, approval_id: str) -> bool:
        async with self._lock:
            if approval_id in self._processed_approvals:
                logger.warning(f"Duplicate approval ignored: {approval_id}")
                return False
            self._processed_approvals.add(approval_id)
            return True
```

Worker idempotency:
```python
# Dosya zaten done ise yeniden yazma
async def worker_node(state: OrchestratorState) -> dict:
    file_registry = state.get("file_registry", {})
    
    if file_registry.get(target_file) == "done":
        logger.info(f"Dosya zaten tamamlanmış, atlıyorum: {target_file}")
        return {}  # State değişikliği yok
    
    # Normal yazma akışı...
```

---

## References

- `upsert-pattern-skill/SKILL.md` — idempotent DB yazma
- `checkpoint-strategy-review-skill/SKILL.md` — recovery
- `partial-sprint-recovery-skill/SKILL.md` — kısmi recovery
