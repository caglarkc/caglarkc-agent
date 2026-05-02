---
name: file-dependency-detection
description: Coder AI için — Python import analizi ile hangi dosyanın hangi dosyaya bağımlı olduğunu tespit etmek; doğru context_files listesi oluşturmak.
---

## Purpose

`repository.py` içinde `from src.storage.models import Sprint` varsa `models.py` bağımlıdır.
Import analizi bu bağımlılıkları otomatik tespit eder.
Worker doğru context dosyalarını prompt'a ekleyebilir.

---

## When to Apply

- Dispatcher context_files listesi oluştururken
- Yeni görev için hangi dosyaların bağlam olarak gerektiğini belirlerken
- Bağımlılık grafiği çizilirken

---

## Rules

- Sadece `src/` altındaki iç import'lar takip edilir.
- Harici kütüphane import'ları atlanır.
- `ast.parse` ile static analiz — runtime gerektirmez.
- Döngüsel bağımlılık: max 2 derinlik analiz edilir.

---

## Guidelines

```python
import ast
from pathlib import Path

def extract_local_imports(
    file_path: str,
    src_root: str = "src",
) -> list[str]:
    """Dosyadaki yerel import'ları döndürür."""
    try:
        with open(file_path) as f:
            source = f.read()
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith(src_root):
                # src.storage.models → src/storage/models.py
                parts = module.split(".")
                candidate = Path(*parts).with_suffix(".py")
                if candidate.exists():
                    imports.append(str(candidate))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(src_root):
                    parts = alias.name.split(".")
                    candidate = Path(*parts).with_suffix(".py")
                    if candidate.exists():
                        imports.append(str(candidate))
    
    return list(set(imports))

def build_context_file_list(
    target_file: str,
    all_project_files: list[str],
    max_depth: int = 2,
) -> list[str]:
    """Hedef dosyanın bağımlı olduğu dosyaları döndürür."""
    context = set()
    to_check = [target_file]
    
    for _ in range(max_depth):
        next_check = []
        for f in to_check:
            deps = extract_local_imports(f)
            new_deps = [d for d in deps if d not in context]
            context.update(new_deps)
            next_check.extend(new_deps)
        to_check = next_check
    
    return [f for f in context if f != target_file]
```

---

## References

- `file-context-loader-skill/SKILL.md` — dosya yükleme
- `task-dependency-ordering-skill/SKILL.md` — görev sırası
- `queue-entry-construction-skill/SKILL.md` — kuyruk girişi
