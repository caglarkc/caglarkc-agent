---
name: file-context-loader
description: Coder AI için — worker node'da kod üretmeden önce bağımlı dosyaların içeriğini okuyarak LLM prompt'una eklemek.
---

## Purpose

Bağlam olmadan kod üretmek tutarsız sonuç verir.
`repository.py` yazılırken `models.py`'nin içeriği prompt'ta olmalı.
Bağımlı dosyaları yükleyen merkezi loader her worker'da tekrarı önler.

---

## When to Apply

- Worker node kod üretmeden önce
- `context_files` listesi dolu olan görevlerde
- LLM'e mevcut kod yapısı gösterilmesi gerektiğinde

---

## Rules

- Sadece `context_files` listesindeki dosyalar yüklenir.
- Dosya yoksa: uyarı loglanır, prompt'a dahil edilmez.
- Toplam context: `MAX_CONTEXT_CHARS` ile sınırlandırılır.
- Binary dosyalar yüklenmez — sadece metin dosyaları.

---

## Guidelines

```python
import aiofiles
from pathlib import Path

MAX_CONTEXT_CHARS = 4000
TEXT_EXTENSIONS = {".py", ".md", ".toml", ".yaml", ".json", ".txt"}

async def load_context_files(
    file_paths: list[str],
    max_chars: int = MAX_CONTEXT_CHARS,
) -> dict[str, str]:
    loaded = {}
    total_chars = 0
    
    for file_path in file_paths:
        path = Path(file_path)
        
        if path.suffix not in TEXT_EXTENSIONS:
            logger.debug(f"Binary dosya atlandı: {file_path}")
            continue
        
        if not path.exists():
            logger.warning(f"Context dosyası bulunamadı: {file_path}")
            continue
        
        remaining = max_chars - total_chars
        if remaining <= 0:
            logger.warning("Context limit aşıldı, dosyalar atlandı")
            break
        
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read(remaining)
            
            if len(content) == remaining:
                content += "\n... [dosya kırpıldı]"
            
            loaded[file_path] = content
            total_chars += len(content)
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Dosya okunamadı: {file_path}: {e}")
    
    return loaded
```

Worker'da kullanım:
```python
context = await load_context_files(entry.context_files)
messages = build_coder_prompt(
    task_description=entry.task_description,
    file_path=entry.file_path,
    context_files=context,
)
```

---

## References

- `worker-node-implementation-skill/SKILL.md` — worker
- `context-window-management-skill/SKILL.md` — token yönetimi
- `prompt-template-construction-skill/SKILL.md` — prompt
