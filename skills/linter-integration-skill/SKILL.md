---
name: linter-integration
description: Coder AI için — ruff ve mypy gibi araçları koda entegre etmek; lint hatalarını otomatik düzeltmek veya CI'ya eklemek.
---

## Purpose

Kod stili tutarsızlığı code review sürecini yavaşlatır.
Otomatik lint, stil sorunlarını insan görmeden düzeltir.
mypy tip hatalarını compile-time'da yakalar.

---

## When to Apply

- Yeni dosya yazıldıktan sonra validator node'da lint çalıştırılırken
- `pre-commit` hook konfigüre edilirken
- CI pipeline'a lint adımı eklenirken

---

## Rules

- `ruff check --fix`: otomatik düzeltilebilir hataları düzeltir.
- `ruff format`: kod formatını standartlaştırır.
- `mypy --strict`: tip kontrol, opsiyonel (yavaş).
- Lint başarısız: sprint tamamlanmaz.
- `# noqa: E501` sadece gerekçeyle — toplu suppression yasak.

---

## Guidelines

```python
# src/core/linting.py
async def run_linter(
    files: list[str],
    fix: bool = True,
) -> tuple[bool, str]:
    """Returns (passed, output)."""
    cmd = ["ruff", "check"]
    if fix:
        cmd.append("--fix")
    cmd.extend(files)
    
    try:
        stdout, _ = await run_command(cmd)
        return True, stdout
    except SubprocessError as e:
        return False, e.stderr

async def run_formatter(files: list[str]) -> None:
    await run_command(["ruff", "format"] + files)

async def run_type_check(files: list[str]) -> tuple[bool, str]:
    try:
        stdout, _ = await run_command(["mypy"] + files + ["--ignore-missing-imports"])
        return True, stdout
    except SubprocessError as e:
        return False, e.stderr
```

`pre-commit` konfigürasyonu (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Validator'da kullanım:
```python
passed, output = await run_linter(done_files)
if not passed:
    return {"review_result": "rejected", "review_comments": [output]}
```

---

## References

- `validator-node-implementation-skill/SKILL.md` — validator
- `subprocess-async-skill/SKILL.md` — komut çalıştırma
- `code-review-checklist-skill/SKILL.md` — review kriterleri
