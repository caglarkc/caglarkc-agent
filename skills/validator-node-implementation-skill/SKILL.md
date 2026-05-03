---
name: validator-node-implementation
description: Coder AI için — LangGraph validator node'unu implemente etmek; üretilen dosyaların syntax doğruluğunu ve temel kural uyumunu otomatik kontrol etmek.
---

## Purpose

Reviewer LLM çağrısı öncesinde basit otomatik kontroller yapılır.
Syntax hatası varsa LLM reviewer'a gerek kalmadan reddedilir.
Hızlı ve ucuz kontroller (ruff, py_compile) önde çalışır.

---

## When to Apply

- `src/graph/nodes/validator.py` yazılırken
- Executor → reviewer arasına otomatik kontrol eklenirken
- Linter veya syntax checker entegrasyonu gerektiğinde

---

## Rules

- Validator, LLM çağrısı yapmaz — sadece araç çalıştırır.
- `py_compile`: syntax kontrol, çok hızlı.
- `ruff check`: linting, hızlı.
- Kritik hata varsa: `review_result = "rejected"`, reviewer atlanır.
- Tüm kontroller geçerse: reviewer node'a gönderilir.

---

## Guidelines

```python
# src/graph/nodes/validator.py
import py_compile
import ast

async def validator_node(state: OrchestratorState) -> OrchestratorState:
    file_registry = state.get("file_registry", {})
    done_files = [p for p, s in file_registry.items() if s == "done"]
    
    validation_errors = []
    
    for file_path in done_files:
        if not file_path.endswith(".py"):
            continue
        
        # Syntax kontrolü
        error = _check_python_syntax(file_path)
        if error:
            validation_errors.append(f"{file_path}: {error}")
    
    if validation_errors:
        return {
            "review_result": "rejected",
            "review_comments": validation_errors,
            "validation_passed": False,
        }
    
    # Ruff kontrolü (subprocess)
    try:
        await run_command(["ruff", "check", "--select", "E,F"] + done_files)
    except SubprocessError as e:
        return {
            "review_result": "rejected",
            "review_comments": [f"Ruff: {e.stderr}"],
            "validation_passed": False,
        }
    
    return {"validation_passed": True}

def _check_python_syntax(file_path: str) -> str | None:
    try:
        with open(file_path) as f:
            source = f.read()
        ast.parse(source)
        return None
    except SyntaxError as e:
        return f"SyntaxError satır {e.lineno}: {e.msg}"
```

---

## References

- `reviewer-node-implementation-skill/SKILL.md` — reviewer
- `subprocess-async-skill/SKILL.md` — araç çalıştırma
- `node-function-signature-skill/SKILL.md` — node imzası
