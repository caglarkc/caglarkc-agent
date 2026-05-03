---
name: fixture-factory-pattern
description: Coder AI için — pytest fixture'larında test verisi üreten factory fonksiyonları yazmak; tekrar eden test setup kodunu merkezileştirmek.
---

## Purpose

Test verisi oluşturma kodu her test dosyasında tekrarlanırsa bakım zorlaşır.
Factory fixture'ları merkezi test nesneleri üretir.
Farklı test senaryoları için özelleştirilebilir varsayılan değerler sağlar.

---

## When to Apply

- Aynı model nesnesi (Sprint, Project, Task) birden fazla test dosyasında gerektiğinde
- `conftest.py` fixture'ları yazılırken
- Test setup kodu 5+ satır olduğunda

---

## Rules

- Factory fixture: callable döndürür — `factory()` şeklinde kullanılır.
- Varsayılan değerler: anlamlı test değerleri (UUID değil `"test-sprint-1"`).
- DB fixture: `tmp_path` ile geçici DB — gerçek DB'ye dokunulmaz.
- `scope="session"` sadece paylaşılan read-only fixture'lar için.

---

## Guidelines

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from datetime import datetime

@pytest.fixture
def make_project():
    def _factory(
        project_id: str = "test-project",
        name: str = "Test Projesi",
        status: str = "active",
    ) -> Project:
        return Project(
            project_id=project_id,
            name=name,
            status=status,
            created_at=datetime.utcnow(),
        )
    return _factory

@pytest.fixture
def make_sprint(make_project):
    def _factory(
        sprint_id: str = "test-sprint-1",
        project_id: str = "test-project",
        status: str = "draft",
        tasks: list | None = None,
    ) -> Sprint:
        return Sprint(
            sprint_id=sprint_id,
            project_id=project_id,
            status=status,
            tasks=tasks or [],
            created_at=datetime.utcnow(),
        )
    return _factory

@pytest_asyncio.fixture
async def db_repo(tmp_path):
    db_path = str(tmp_path / "test.db")
    repo = ProjectRepository(db_path)
    await repo.initialize()
    yield repo

# Test kullanımı
async def test_create_sprint(db_repo, make_sprint):
    sprint = make_sprint(status="active")
    await db_repo.create_sprint(sprint)
    found = await db_repo.get_sprint(sprint.sprint_id)
    assert found.status == "active"
```

---

## References

- `pytest-async-test-skill/SKILL.md` — async test yazma
- `state-builder-for-tests-skill/SKILL.md` — state builder
- `graph-node-isolation-test-skill/SKILL.md` — node testi
