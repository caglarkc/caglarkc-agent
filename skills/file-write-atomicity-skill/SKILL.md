---
name: file-write-atomicity
description: Coder AI için — üretilen kod dosyasını diske yazarken kısmi yazma ve yarım dosya sorunlarını önlemek için atomik write pattern uygulamak.
---

## Purpose

Worker dosyayı yazarken çökerse yarım dosya kalır — bir sonraki okuma bozuk kod görür.
Temp dosya + rename ile atomik yazma: ya tam var ya hiç yok.
`done` durumuna geçiş dosya yazıldıktan sonra olur — race condition önlenir.

---

## When to Apply

- Worker node'da üretilen kodu diske yazarken
- Büyük dosya içeriği yazılırken (> 1 KB)
- Checkout sonrasında dosya güncellenirken

---

## Rules

- Temp dosyaya yaz (`.tmp` uzantısı), başarılıysa rename.
- Hedef dizin yoksa oluştur (`mkdir -p` eşdeğeri).
- Rename atomik — OS garantisi (POSIX).
- Yazma başarısız olursa temp dosya temizlenir.
- `done` kaydı ancak rename başarılı olduktan sonra.

---

## Guidelines

```python
import asyncio
import aiofiles
from pathlib import Path

async def write_file_atomic(
    file_path: str,
    content: str,
    encoding: str = "utf-8"
) -> None:
    target = Path(file_path)
    temp_path = target.with_suffix(target.suffix + ".tmp")
    
    # Hedef dizini oluştur
    target.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Temp dosyaya yaz
        async with aiofiles.open(temp_path, "w", encoding=encoding) as f:
            await f.write(content)
            await f.flush()
        
        # Atomik rename
        temp_path.rename(target)
        logger.debug(f"Dosya yazıldı: {file_path}")
    
    except Exception as e:
        # Temp dosyayı temizle
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise IOError(f"Dosya yazılamadı: {file_path}: {e}") from e


# Worker node'da kullanım
async def write_generated_code(
    file_path: str,
    code_content: str,
    file_registry: dict[str, str]
) -> dict[str, str]:
    await write_file_atomic(file_path, code_content)
    
    # Sadece yazma başarılıysa done yap
    updated_registry = dict(file_registry)
    updated_registry[file_path] = "done"
    return updated_registry
```

---

## References

- `worker-node-implementation-skill/SKILL.md` — worker
- `file-status-state-machine-skill/SKILL.md` — dosya durumu
- `async-context-manager-skill/SKILL.md` — async kaynak yönetimi
