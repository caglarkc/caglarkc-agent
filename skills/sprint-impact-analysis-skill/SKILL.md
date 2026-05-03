---
name: sprint-impact-analysis
description: Planner AI için — bir görev veya değişikliğin diğer modülleri nasıl etkileyeceğini önceden analiz etmek.
---

## Purpose

Tek dosya değişikliği başka dosyaları bozabilir.
Etki analizi: değiştirilen dosyayı import eden modülleri tespit eder.
Risk: "bu değişiklik 5 dosyayı etkiliyor" önceden bilinir.

---

## When to Apply

- Sprint planı oluşturulurken etki tahmini istendiğinde
- Büyük refactor öncesinde kapsam belirlenmesi gerektiğinde
- Kullanıcı "bu değişiklik neyi etkiler?" diye sorduğunda

---

## Rules

- Analiz: proje dosya ağacında import taraması.
- Doğrudan etki: değiştirilen dosyayı import eden.
- Dolaylı etki: doğrudan etkileneni import eden (maks 2 seviye).
- Sonuç: etki derecesi ile görev risk puanı güncellenir.

---

## Guidelines

```python
import ast
from pathlib import Path

def find_importers(
    changed_file: str,
    project_root: str,
    depth: int = 2,
) -> dict[str, int]:
    module_name = _path_to_module(changed_file, project_root)
    result: dict[str, int] = {}
    _find_importers_recursive(module_name, project_root, result, depth, set())
    return result

def _path_to_module(file_path: str, root: str) -> str:
    rel = Path(file_path).relative_to(root)
    return str(rel).replace("/", ".").replace(".py", "")

def _find_importers_recursive(
    module: str,
    root: str,
    found: dict[str, int],
    depth: int,
    visited: set[str],
) -> None:
    if depth == 0 or module in visited:
        return
    visited.add(module)
    for py_file in Path(root).rglob("*.py"):
        try:
            source = py_file.read_text(errors="ignore")
            tree   = ast.parse(source)
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported = node.module or ""
                if module in imported or imported.endswith(module.split(".")[-1]):
                    path = str(py_file)
                    found[path] = found.get(path, 0) + 1
                    _find_importers_recursive(
                        _path_to_module(path, root), root, found, depth - 1, visited
                    )

def format_impact_report(importers: dict[str, int]) -> str:
    if not importers:
        return "Bu değişiklik başka modülü etkilemiyor."
    lines = [f"Etkilenen modüller ({len(importers)}):"]
    for path, count in sorted(importers.items(), key=lambda x: -x[1]):
        lines.append(f"  - {path} ({count} import)")
    return "\n".join(lines)
```

---

## References

- `file-dependency-detection-skill/SKILL.md` — dosya bağımlılığı
- `sprint-risk-register-skill/SKILL.md` — risk kaydı
- `sprint-what-if-analysis-skill/SKILL.md` — what-if analizi
