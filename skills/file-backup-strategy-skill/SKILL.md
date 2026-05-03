---
name: file-backup-strategy
description: Coder AI için — worker kod yazmadan önce mevcut dosyayı yedeklemek; yazma başarısız olduğunda orijinal dosyayı geri yüklemek.
---

## Purpose

Worker mevcut dosyayı üzerine yazarken hata olursa orijinal içerik kaybolur.
Backup, yazma öncesinde `dosya.py.bak` kopyası oluşturur.
Başarılı yazma sonrası backup silinir; başarısız olursa geri yüklenir.

---

## When to Apply

- Mevcut dosya üzerine yazılırken (yeni dosya değil)
- Sprint sırasında var olan kod güncellenmesi gerektiğinde
- Rollback mekanizması eklenmesi gerektiğinde

---

## Rules

- Backup: `{filename}.bak` — aynı dizinde.
- Yeni dosya (mevcut yok): backup gerekmez.
- Yazma başarılı: backup silinir.
- Yazma başarısız: backup geri yüklenir, hata fırlatılır.
- Backup başarısız: uyarı loglanır ama yazma devam eder.

---

## Guidelines

```python
from contextlib import asynccontextmanager
from pathlib import Path
import aiofiles
import shutil

@asynccontextmanager
async def file_backup(file_path: str):
    """Dosya yazma öncesi backup alır, hata durumunda geri yükler."""
    path = Path(file_path)
    backup_path = path.with_suffix(path.suffix + ".bak")
    has_backup = False
    
    # Mevcut dosya varsa backup al
    if path.exists():
        try:
            shutil.copy2(str(path), str(backup_path))
            has_backup = True
            logger.debug(f"Backup alındı: {backup_path}")
        except OSError as e:
            logger.warning(f"Backup alınamadı: {e} — devam ediliyor")
    
    try:
        yield
        # Başarılı — backup'ı temizle
        if has_backup and backup_path.exists():
            backup_path.unlink()
            logger.debug(f"Backup temizlendi: {backup_path}")
    
    except Exception:
        # Başarısız — geri yükle
        if has_backup and backup_path.exists():
            try:
                shutil.copy2(str(backup_path), str(path))
                backup_path.unlink()
                logger.info(f"Dosya geri yüklendi: {file_path}")
            except OSError as restore_err:
                logger.error(f"Geri yükleme başarısız: {restore_err}")
        raise

# Kullanım
async def safe_write_file(file_path: str, content: str) -> None:
    async with file_backup(file_path):
        await write_file_atomic(file_path, content)
```

---

## References

- `file-write-atomicity-skill/SKILL.md` — atomik yazma
- `rollback-strategy-skill/SKILL.md` — rollback
- `async-context-manager-skill/SKILL.md` — context manager
