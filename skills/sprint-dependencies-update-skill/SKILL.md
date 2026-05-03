---
name: sprint-dependencies-update
description: Coder AI için — sprint sırasında yeni Python bağımlılıkları tespit etmek ve pyproject.toml / requirements.txt'e otomatik eklemek.
---

## Purpose

Üretilen kod yeni kütüphane kullanıyorsa requirements güncellenmelidir.
Otomatik bağımlılık tespiti: import ifadelerinden yeni paketleri bulur.
Bağımlılık listesi güncel tutulur — kurulum adımı atlanmaz.

---

## When to Apply

- Yeni dosya üretildiğinde import'lar analiz edilirken
- Sprint sonunda eksik bağımlılıklar kontrol edilirken
- Validator "ModuleNotFoundError" bildirdiğinde

---

## Rules

- stdlib ve mevcut paketler atlanır.
- Yeni paket: pyproject.toml `[project.dependencies]`'e eklenir.
- Versiyon: `>=current` olarak pinlenir.
- Manuel onay: gerekli değil — otomatik ekle, logla.

---

## Guidelines

```python
import ast
import sys
import importlib.util
from pathlib import Path

STDLIB_MODULES = set(sys.stdlib_module_names)

def extract_third_party_imports(code: str) -> set[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module:
                imports.add(node.module.split(".")[0])
    
    return {
        pkg for pkg in imports
        if pkg not in STDLIB_MODULES
        and not _is_installed(pkg)
        and not pkg.startswith("_")
    }

def _is_installed(package: str) -> bool:
    return importlib.util.find_spec(package) is not None

def update_requirements(
    new_packages: set[str],
    req_file: str = "requirements.txt",
) -> int:
    path = Path(req_file)
    existing = set()
    if path.exists():
        for line in path.read_text().splitlines():
            pkg = line.split(">=")[0].split("==")[0].strip().lower()
            if pkg:
                existing.add(pkg)
    
    added = 0
    with path.open("a") as f:
        for pkg in sorted(new_packages):
            if pkg.lower() not in existing:
                f.write(f"\n{pkg}>=0.1")
                added += 1
    return added
```

---

## References

- `env-file-setup-skill/SKILL.md` — ortam kurulumu
- `python-packaging-skill/SKILL.md` — Python paketleme
- `code-import-resolver-skill/SKILL.md` — import çözücü
