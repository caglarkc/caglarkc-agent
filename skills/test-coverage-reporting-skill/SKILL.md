---
name: test-coverage-reporting
description: Coder AI için — pytest-cov ile test kapsamı raporunu çalıştırmak; düşük kapsama sahip modülleri tespit etmek.
---

## Purpose

Hangi kodun test edildiği bilinmezse güvenle değişiklik yapılamaz.
Coverage raporu kritik modüllerdeki test boşluklarını gösterir.
%100 hedef değil — kritik yollar (%80+) öncelik.

---

## When to Apply

- Sprint sonunda test kapsamı değerlendirilirken
- Yeni modül eklendiğinde coverage baseline kurulurken
- CI pipeline'a coverage gate eklenirken

---

## Rules

- Hedef: kritik modüller (`src/core/`, `src/graph/`) %80+ kapsama.
- Coverage raporu: HTML veya terminal.
- Branch coverage aktif edilir (`--cov-branch`).
- Test olmayan dosyalar için `# pragma: no cover` yorumu gerekçeyle eklenir.

---

## Guidelines

```bash
# Terminal raporu
pytest tests/ --cov=src --cov-report=term-missing --cov-branch

# HTML raporu
pytest tests/ --cov=src --cov-report=html:coverage_report

# Minimum eşik kontrolü (CI için)
pytest tests/ --cov=src --cov-fail-under=70
```

`pyproject.toml` konfigürasyonu:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["src"]
omit = [
    "src/interfaces/telegram/*",  # E2E test ayrı
    "**/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
show_missing = true
```

Coverage yorumu kullanımı:
```python
if sys.platform == "win32":  # pragma: no cover
    # Windows'a özgü kod — CI'da test edilmiyor
    ...
```

---

## References

- `pytest-async-test-skill/SKILL.md` — async test
- `test-strategy-planning-skill/SKILL.md` — test planı
- `acceptance-criteria-definition-skill/SKILL.md` — kabul kriterleri
