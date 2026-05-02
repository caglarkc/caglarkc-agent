---
name: code-import-resolver
description: Coder AI için — üretilen koddaki import hatalarını tespit edip çözmek; eksik veya yanlış import'ları düzeltmek.
---

## Purpose

LLM ürettiği kodda import eksik veya yanlış modül adı kullanılabilir.
Import resolver: sözdizimi hatalarını yakalar, doğru modül yolunu bulur.
Validator node'dan önce çalışarak kolay hataları otomatik düzeltir.

---

## When to Apply

- Üretilen kod `ImportError` veya `ModuleNotFoundError` verdiğinde
- Validator node import hatasını raporladığında
- Kod birleştirme sonrası import sırası düzeltilirken

---

## Rules

- stdlib modülleri: otomatik düzeltilebilir (bilinen yerler).
- Üçüncü taraf: `requirements.txt` veya `pyproject.toml` kontrol edilir.
- Yerel modül: proje dosya yapısından yol çıkarılır.
- Düzeltilemeyen import: hata olarak raporlanır, retry tetiklenir.

---

## Guidelines

```python
import ast
from pathlib import Path

COMMON_STDLIB_ALIASES = {
    "datetime": "from datetime import datetime",
    "uuid4":    "from uuid import uuid4",
    "dataclass": "from dataclasses import dataclass, field",
    "TypedDict": "from typing import TypedDict",
    "asyncio":  "import asyncio",
}

def extract_undefined_names(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    defined = set()
    used    = set()
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
    
    return list(used - defined - set(dir(__builtins__)))

def suggest_imports(undefined: list[str], project_root: str) -> dict[str, str]:
    suggestions = {}
    for name in undefined:
        if name in COMMON_STDLIB_ALIASES:
            suggestions[name] = COMMON_STDLIB_ALIASES[name]
        else:
            # Proje içinde ara
            found = _find_in_project(name, project_root)
            if found:
                suggestions[name] = f"from {found} import {name}"
    return suggestions

def _find_in_project(name: str, root: str) -> str | None:
    for py_file in Path(root).rglob("*.py"):
        if py_file.read_text(errors="ignore").find(f"def {name}") != -1 or \
           py_file.read_text(errors="ignore").find(f"class {name}") != -1:
            rel = py_file.relative_to(root)
            return str(rel).replace("/", ".").replace(".py", "")
    return None
```

---

## References

- `code-review-checklist-skill/SKILL.md` — kod inceleme
- `linter-integration-skill/SKILL.md` — linter entegrasyonu
- `validator-node-implementation-skill/SKILL.md` — validator node
