---
name: pytest-async-test
description: Coder AI için — pytest ile async fonksiyon ve LangGraph node'larını test etme; asyncio mark, fixture ve mock kullanımı.
---

## Purpose

Async fonksiyonların pytest ile doğru test edilmesini sağlar.
LangGraph node'larının izole edilmiş birim testlerini standartlaştırır.
Test setup/teardown için async fixture pattern'ını uygular.

---

## When to Apply

- Yeni async fonksiyon veya node için test dosyası yazılırken
- `tests/` dizinine yeni test modülü eklenirken

---

## Rules

- `@pytest.mark.asyncio` decorator'ı async test fonksiyonlarında zorunlu.
- `pytest-asyncio` kütüphanesi `pyproject.toml`'da olmalı.
- Her test kendi izole state'iyle çalışır (shared state yok).
- Mock'lar `unittest.mock.AsyncMock` ile yapılır.
- Test dosyası ismi: `test_<modül_adı>.py`.
- Test fonksiyonu ismi: `test_<davranış>_<koşul>`.

---

## Guidelines

Temel async test:
```python
import pytest
from unittest.mock import AsyncMock, patch

# conftest.py
@pytest.fixture
def anyio_backend():
    return "asyncio"

# Veya pytest.ini / pyproject.toml'da:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"


# test_planner.py
import pytest
from src.graph.nodes.planner import planner_node
from src.graph.state import build_initial_state

@pytest.mark.asyncio
async def test_planner_node_generates_draft_plan():
    # Arrange
    state = build_initial_state(
        project_id="test-project",
        task="Planner'a retry ekle"
    )
    
    mock_plan = {
        "summary": "Retry ekle",
        "files": ["src/graph/nodes/planner.py"],
        "dependencies": {}
    }
    
    with patch(
        "src.graph.nodes.planner.manager_service.process_turn",
        new_callable=AsyncMock,
        return_value=mock_plan
    ):
        # Act
        result = await planner_node(state)
    
    # Assert
    assert "draft_plan" in result
    assert result["draft_plan"]["summary"] == "Retry ekle"
    assert "approval_request" in result


@pytest.mark.asyncio
async def test_planner_node_handles_llm_error():
    state = build_initial_state("test", "task")
    
    with patch(
        "src.graph.nodes.planner.manager_service.process_turn",
        new_callable=AsyncMock,
        side_effect=Exception("LLM failed")
    ):
        result = await planner_node(state)
    
    assert "errors" in result
    assert len(result["errors"]) > 0
```

Async fixture:
```python
@pytest.fixture
async def repository(tmp_path):
    db_path = str(tmp_path / "test.db")
    repo = DatabaseRepository(db_path)
    await repo.initialize()
    yield repo
    # cleanup otomatik (tmp_path ile)
```

---

## References

- `mock-llm-response-skill/SKILL.md` — LLM mock
- `mock-event-bus-skill/SKILL.md` — event bus mock
- `state-builder-for-tests-skill/SKILL.md` — test state
