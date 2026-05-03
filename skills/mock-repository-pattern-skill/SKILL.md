---
name: mock-repository-pattern
description: Coder AI için — testlerde gerçek DB yerine AsyncMock tabanlı repository mock'u kullanmak; DB olmadan unit test yazmak.
---

## Purpose

Unit test için gerçek DB bağlantısı kurmak yavaş ve kırılgandır.
`AsyncMock(spec=ProjectRepository)` ile gerçek interface'i koruyan mock oluşturulur.
Mock davranışı özelleştirilerek farklı senaryolar test edilir.

---

## When to Apply

- Node veya servis unit testi yazılırken
- DB kurulumu olmadan test çalıştırmak gerektiğinde
- Repository metodunun farklı dönüşleri test edilirken

---

## Rules

- `spec=` parametresi zorunlu — metodları gerçek interface'e kilitler.
- Metod dönüşü: `mock.method.return_value = ...` veya `AsyncMock(return_value=...)`.
- Hata senaryosu: `mock.method.side_effect = SomeException`.
- `assert_called_once_with()` ile çağrı doğrulaması yapılır.

---

## Guidelines

```python
from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.fixture
def mock_repo():
    repo = AsyncMock(spec=ProjectRepository)
    # Varsayılan dönüşler
    repo.get_project.return_value = Project(
        project_id="test-project",
        name="Test",
        status="active",
        created_at=datetime.utcnow(),
    )
    repo.get_sprint.return_value = None  # sprint yok
    repo.create_sprint.return_value = None  # void
    return repo

async def test_planner_creates_sprint(mock_repo, mock_llm):
    node = make_planner_node(mock_repo, mock_llm)
    state = build_initial_state(project_id="test-project")
    
    result = await node(state)
    
    # Sprint oluşturuldu mu?
    mock_repo.create_sprint.assert_called_once()
    created_sprint = mock_repo.create_sprint.call_args[0][0]
    assert created_sprint.project_id == "test-project"

async def test_planner_handles_db_error(mock_repo, mock_llm):
    mock_repo.create_sprint.side_effect = aiosqlite.Error("DB hatası")
    
    node = make_planner_node(mock_repo, mock_llm)
    state = build_initial_state(project_id="test-project")
    
    with pytest.raises(aiosqlite.Error):
        await node(state)

# Repository dönüş listesi
async def test_project_listing(mock_repo):
    mock_repo.list_projects.return_value = [
        Project(project_id="p1", name="Proje 1", ...),
        Project(project_id="p2", name="Proje 2", ...),
    ]
    projects = await mock_repo.list_projects()
    assert len(projects) == 2
```

---

## References

- `pytest-async-test-skill/SKILL.md` — async test
- `mock-llm-response-skill/SKILL.md` — LLM mock
- `dependency-injection-patterns-skill/SKILL.md` — DI
