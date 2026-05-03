---
name: code-dead-code-detection
description: Coder AI için — üretilen kodda kullanılmayan fonksiyonlar, değişkenler ve import'ları tespit etmek.
---

## Purpose

LLM bazen kullanılmayan yardımcı fonksiyon veya import üretir.
Ölü kod: bakımı zorlaştırır, kafa karıştırır.
Otomatik tespit: ruff F401/F841 + AST analizi ile bulunur.

---

## When to Apply

- Reviewer node kod kalitesini değerlendirirken
- Refactor sonrası artık kod temizlenirken
- Sprint bitiminde dosya boyutu büyükse

---

## Rules

- Kullanılmayan import: F401 — hata olarak işaretlenir.
- Kullanılmayan değişken: F841 — uyarı.
- Kullanılmayan fonksiyon: modülden referans yok — düşük öncelikli uyarı.
- Otomatik silme: yalnızca import'lar için (ruff --fix).

---

## Guidelines

```python
import ast
import subprocess

def detect_unused_imports(file_path: str) -> list[dict]:
    result = subprocess.run(
        ["ruff", "check", "--select=F401", "--output-format=json", file_path],
        capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):
        return []
    import json
    try:
        findings = json.loads(result.stdout)
        return [
            {
                "line":    f["location"]["row"],
                "message": f["message"],
                "fix":     f.get("fix") is not None,
            }
            for f in findings
        ]
    except (json.JSONDecodeError, KeyError):
        return []

def detect_unused_variables(code: str) -> list[dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    assigned = {}
    used     = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    assigned[target.id] = getattr(target, "lineno", 0)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
    
    return [
        {"name": name, "line": line, "type": "unused_variable"}
        for name, line in assigned.items()
        if name not in used
    ]

def fix_unused_imports(file_path: str) -> bool:
    result = subprocess.run(
        ["ruff", "check", "--select=F401", "--fix", file_path],
        capture_output=True,
    )
    return result.returncode == 0
```

---

## References

- `linter-integration-skill/SKILL.md` — linter entegrasyonu
- `code-refactor-suggestion-skill/SKILL.md` — refactor önerileri
- `code-review-checklist-skill/SKILL.md` — kod inceleme
