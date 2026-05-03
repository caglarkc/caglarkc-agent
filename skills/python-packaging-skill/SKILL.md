---
name: python-packaging
description: Coder AI için — pyproject.toml ile Python paketini doğru yapılandırmak; bağımlılıkları, entry point'leri ve geliştirme araçlarını tanımlamak.
---

## Purpose

Proje düzgün paketlenmezse `pip install -e .` çalışmaz.
`pyproject.toml` modern Python paket standardıdır.
Bağımlılık versiyonları sabitlenmezse environment farklılıkları oluşur.

---

## When to Apply

- Yeni proje kurulurken
- `pyproject.toml` eksik veya güncel değilken
- Yeni bağımlılık eklenirken

---

## Rules

- `[project]` bölümü zorunlu: name, version, dependencies.
- Bağımlılık versiyonu: `>=x.y` (minimum) veya `==x.y.z` (sabit).
- Dev bağımlılıkları: `[project.optional-dependencies]` altında.
- Entry point: `[project.scripts]`.
- `uv` veya `pip-tools` ile lock file oluşturulur.

---

## Guidelines

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "caglarkc-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=0.2.0",
    "langchain-google-genai>=2.0.0",
    "langchain-ollama>=0.2.0",
    "aiosqlite>=0.20.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-telegram-bot>=21.0",
    "httpx>=0.27.0",
    "aiofiles>=24.0.0",
    "click>=8.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4.0",
]

[project.scripts]
caglarkc = "src.interfaces.cli.commands:cli"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## References

- `settings-validation-skill/SKILL.md` — env config
- `env-file-setup-skill/SKILL.md` — env dosyası
- `project-file-structure-skill/SKILL.md` — dosya yapısı
