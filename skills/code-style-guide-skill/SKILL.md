---
name: code-style-guide
description: Coder AI için — proje kod stilini tanımlamak ve uygulamak; tutarlı Python kodu üretmek.
---

## Purpose

LLM farklı çağrılarda farklı stil kullanır — camelCase, snake_case karışımı olur.
Stil rehberi üretilen her dosyada aynı konvansiyonları uygular.
Otomatik linter (ruff, black) ile doğrulanır.

---

## When to Apply

- Yeni dosya üretilmeden önce stil kısıtlamaları tanımlanırken
- Üretilen kod linter'dan geçirilirken
- Code review'da stil sorunları düzeltilirken

---

## Rules

- Satır uzunluğu: maks 100 karakter.
- İsimlendirme: snake_case (değişken, fonksiyon), PascalCase (sınıf), UPPER_CASE (sabit).
- Import sırası: stdlib → third-party → local.
- Type hint: her public fonksiyonda zorunlu.
- Docstring: yalnızca public API'de, tek satır.

---

## Guidelines

```python
# ruff.toml veya pyproject.toml konfigürasyonu
RUFF_CONFIG = """
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]
ignore = ["E501"]  # line-length ruff kendisi yönetir

[tool.ruff.lint.isort]
known-first-party = ["caglarkc_agent"]
"""

# Üretilen koda eklenecek stil direktifi (prompt'a eklenir)
STYLE_PROMPT_FRAGMENT = """
Kod yazarken şu kurallara uy:
- snake_case değişken ve fonksiyon isimleri
- PascalCase sınıf isimleri
- Tüm public fonksiyonlarda type hint
- Import sırası: stdlib, üçüncü taraf, yerel
- Satır uzunluğu maks 100 karakter
- Gereksiz yorum ekleme
"""

import subprocess

def run_linter(file_path: str) -> tuple[bool, str]:
    result = subprocess.run(
        ["ruff", "check", "--fix", file_path],
        capture_output=True, text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr

def run_formatter(file_path: str) -> bool:
    result = subprocess.run(
        ["ruff", "format", file_path],
        capture_output=True,
    )
    return result.returncode == 0
```

---

## References

- `linter-integration-skill/SKILL.md` — linter entegrasyonu
- `code-review-checklist-skill/SKILL.md` — kod inceleme listesi
- `code-generation-quality-check-skill/SKILL.md` — kalite kontrolü
