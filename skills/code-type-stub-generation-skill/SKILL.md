---
name: code-type-stub-generation
description: Coder AI için — üretilen modüller için .pyi tip stub dosyaları oluşturmak; dış kullanıcılara tip bilgisi sağlamak.
---

## Purpose

Dinamik Python kodu IDE'de tip bilgisi olmadan tamamlanamaz.
.pyi stub dosyaları: sadece imzaları içerir, implement etmez.
Kütüphane veya plugin arayüzü dış kullanıcılara tip güvenliği sağlar.

---

## When to Apply

- Public API modülü üretildiğinde
- LangGraph node imzaları tiplendirilirken
- Harici kullanım için paket hazırlanırken

---

## Rules

- Stub: yalnızca public fonksiyon ve sınıf imzaları.
- Gövde: `...` (ellipsis).
- Dosya adı: `module.pyi` — kaynak dosyayla aynı konumda.
- Overload: polimorfik fonksiyonlar için `@overload` kullanılır.

---

## Guidelines

```python
import ast
from pathlib import Path

def generate_stub(source_path: str) -> str:
    source = Path(source_path).read_text(encoding="utf-8")
    tree   = ast.parse(source)
    lines  = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0:
            names = ", ".join(a.name for a in node.names)
            lines.append(f"from {node.module} import {names}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                lines.append(f"import {alias.name}")

    lines.append("")

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            lines.append(f"class {node.name}:")
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    prefix = "async def " if isinstance(item, ast.AsyncFunctionDef) else "def "
                    sig    = ast.unparse(item.args)
                    ret    = f" -> {ast.unparse(item.returns)}" if item.returns else ""
                    lines.append(f"    {prefix}{item.name}({sig}){ret}: ...")
            lines.append("")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
            sig    = ast.unparse(node.args)
            ret    = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            lines.append(f"{prefix}{node.name}({sig}){ret}: ...")

    return "\n".join(lines)

def write_stub(source_path: str) -> str:
    stub_path = source_path.replace(".py", ".pyi")
    Path(stub_path).write_text(generate_stub(source_path), encoding="utf-8")
    return stub_path
```

---

## References

- `type-alias-definition-skill/SKILL.md` — tip takma adı
- `type-narrowing-patterns-skill/SKILL.md` — tip daraltma
- `python-packaging-skill/SKILL.md` — Python paketleme
