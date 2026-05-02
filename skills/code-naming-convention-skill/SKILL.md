---
name: code-naming-convention
description: Coder AI için — üretilen koddaki isimlendirme hatalarını tespit edip düzeltmek; tutarlı Python isimlendirme sağlamak.
---

## Purpose

LLM bazen camelCase, bazen snake_case kullanır — karışıklık yaratır.
İsimlendirme kontrolü: Python PEP8 kurallarını programatik uygular.
Otomatik düzeltme: yeniden adlandırma AST seviyesinde yapılır.

---

## When to Apply

- Üretilen kodda linter "N" (naming) uyarısı verdiğinde
- Kod inceleme sırasında tutarsız isimler görüldüğünde
- Proje genelinde isimlendirme standardizasyonu istendiğinde

---

## Rules

- Değişken/fonksiyon: snake_case.
- Sınıf: PascalCase.
- Sabit: UPPER_SNAKE_CASE (modül seviyesi).
- Özel: `_single` veya `__double` underscore.

---

## Guidelines

```python
import ast
import re

def check_naming_convention(code: str) -> list[dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    issues = []
    
    for node in ast.walk(tree):
        # Fonksiyon isimleri
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_snake_case(node.name) and not node.name.startswith("_"):
                issues.append({
                    "line":    node.lineno,
                    "name":    node.name,
                    "type":    "function",
                    "fix":     _to_snake_case(node.name),
                    "message": f"Fonksiyon adı snake_case olmalı: '{node.name}' → '{_to_snake_case(node.name)}'",
                })
        
        # Sınıf isimleri
        elif isinstance(node, ast.ClassDef):
            if not _is_pascal_case(node.name):
                issues.append({
                    "line":    node.lineno,
                    "name":    node.name,
                    "type":    "class",
                    "fix":     _to_pascal_case(node.name),
                    "message": f"Sınıf adı PascalCase olmalı: '{node.name}'",
                })
    
    return issues

def _is_snake_case(name: str) -> bool:
    return bool(re.fullmatch(r'[a-z][a-z0-9]*(_[a-z0-9]+)*', name))

def _is_pascal_case(name: str) -> bool:
    return bool(re.fullmatch(r'[A-Z][a-zA-Z0-9]*', name))

def _to_snake_case(name: str) -> str:
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def _to_pascal_case(name: str) -> str:
    return ''.join(word.capitalize() for word in name.split('_'))
```

---

## References

- `code-style-guide-skill/SKILL.md` — kod stil rehberi
- `linter-integration-skill/SKILL.md` — linter entegrasyonu
- `code-ast-manipulation-skill/SKILL.md` — AST manipülasyonu
