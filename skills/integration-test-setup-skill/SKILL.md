---
name: integration-test-setup
description: Coder AI için — LangGraph graph'ının gerçek (veya near-real) bileşenlerle end-to-end çalıştığını doğrulayan integration test altyapısını kurmak.
---

## Purpose

Unit test her node'u izole test eder; integration test akışın bütününü doğrular.
Graph planner→dispatcher→worker akışının doğru çalıştığını kanıtlar.
DB, checkpoint ve event bus gerçek bileşenler olarak kullanılır (LLM mock'lanır).

---

## When to Apply

- Kritik akışlar (plan → onay → kod üretme) test edilirken
- Yeni node eklendiğinde graph akışı doğrulanırken
- Regression test suite oluşturulurken

---

## Rules

- LLM mock'lanır — gerçek API çağrısı yapılmaz.
- DB: `tmp_path` ile geçici — her test izole.
- Checkpoint DB: ayrı geçici dosya.
- Event bus: gerçek instance (in-memory).
- Test timeout: 30 saniye maksimum.

---

## Guidelines

```python
# tests/test_integration/test_plan_flow.py
import pytest
import pytest_asyncio
from pathlib import Path

@pytest_asyncio.fixture
async def integration_setup(tmp_path, mock_llm):
    db_path = str(tmp_path / "test.db")
    checkpoint_path = str(tmp_path / "checkpoint.db")
    
    repo = ProjectRepository(db_path)
    await repo.initialize()
    
    event_bus = EventBus()
    
    # Graph oluştur (gerçek bileşenler, mock LLM)
    graph = build_graph(
        repo=repo,
        llm=mock_llm,
        checkpoint_path=checkpoint_path,
        event_bus=event_bus,
    )
    compiled = graph.compile(
        checkpointer=AsyncSqliteSaver.from_conn_string(checkpoint_path),
        interrupt_before=["dispatcher"],
    )
    
    # Test projesi
    project = Project(project_id="test", name="Test", status="active", ...)
    await repo.create_project(project)
    
    return compiled, repo, event_bus

@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_plan_to_approval_flow(integration_setup):
    compiled, repo, event_bus = integration_setup
    
    config = {"configurable": {"thread_id": "test"}}
    
    # Graph başlat (planner node çalışır, dispatcher'da durur)
    state = await compiled.ainvoke(
        {"project_id": "test", "user_message": "Temel model yaz"},
        config=config,
    )
    
    # Sprint planlandı mı?
    assert state.get("sprint_id") is not None
    assert len(state.get("tasks", [])) > 0
    
    # Onay ver
    await compiled.aupdate_state(
        config=config,
        values={"approval_status": "approved"},
    )
    
    # Devam et
    final_state = await compiled.ainvoke(None, config=config)
    assert final_state.get("sprint_status") == "done"
```

---

## References

- `graph-builder-usage-skill/SKILL.md` — graph oluşturma
- `pytest-async-test-skill/SKILL.md` — async test
- `checkpoint-strategy-review-skill/SKILL.md` — checkpoint
