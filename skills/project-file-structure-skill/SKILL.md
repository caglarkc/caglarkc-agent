---
name: project-file-structure
description: Coder AI için — Python projesinin standart dosya ve dizin yapısını bilmek; yeni dosyaları doğru konuma yerleştirmek.
---

## Purpose

Dosya yanlış dizine yazılırsa import hataları oluşur.
Standart proje yapısı okunabilirliği artırır.
Yeni geliştirici projeye katkı yapabilmek için yapıyı anlamalı.

---

## When to Apply

- Yeni modül veya dosya oluşturulurken
- Import path sorunları çözülürken
- Proje kurulum dökümanı yazılırken

---

## Rules

- `src/` altında uygulama kodu.
- `tests/` altında test kodu — `src/` ile paralel yapı.
- `skills/` sadece SKILL.md — kod yok.
- `src/interfaces/` → dış arayüzler (telegram, cli).
- `src/storage/` → DB katmanı.

---

## Guidelines

```
caglarkc-agent/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Settings (pydantic-settings)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── constants.py         # Sabitler
│   │   ├── recovery.py          # Sprint recovery
│   │   └── event_bus.py         # EventBus singleton
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── builder.py           # Graph assembly
│   │   ├── config.py            # Thread config
│   │   ├── state.py             # OrchestratorState TypedDict
│   │   └── nodes/
│   │       ├── planner.py
│   │       ├── dispatcher.py
│   │       ├── executor.py
│   │       ├── validator.py
│   │       └── reviewer.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── models.py            # Pydantic modeller
│   │   ├── repository.py        # DB CRUD
│   │   └── migrations.py        # DB migration
│   └── interfaces/
│       ├── telegram/
│       │   ├── __init__.py
│       │   └── handlers.py
│       └── cli/
│           ├── __init__.py
│           └── commands.py
├── tests/
│   ├── conftest.py
│   ├── test_nodes/
│   ├── test_storage/
│   └── test_integration/
├── skills/
├── pyproject.toml
├── .env.example
└── README.md
```

---

## References

- `module-boundary-validation-skill/SKILL.md` — modül sınırları
- `import-structure-review-skill/SKILL.md` — import yapısı
- `code-mode-skill/SKILL.md` — genel kurallar
