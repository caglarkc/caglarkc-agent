---
name: mock-event-bus
description: Coder AI için — test sırasında gerçek EventBus yerine mock kullanmak; event emit'lerin doğrulandığı izole testler yazmak.
---

## Purpose

Node veya servis testlerinin gerçek EventBus singleton'a bağımlı olmamasını sağlar.
Emit edilen event'lerin varlığını ve payload'ını test eder.
Test izolasyonu için event bus'ı sıfırlanabilir hale getirir.

---

## When to Apply

- Event emit eden node veya servis test edilirken
- "Bu event emit edildi mi?" doğrulaması gerektiğinde
- EventBus singleton'ın test'ler arasında state taşımasını önlemek için

---

## Rules

- `patch("src.core.event_bus.get_event_bus")` ile mock edilir.
- Mock emit: `AsyncMock` olarak tanımlanır.
- `mock.emit.assert_called_with("event.type", {...})` ile doğrulama.
- Her test kendi mock event bus'ını alır.

---

## Guidelines

Event bus mock:
```python
from unittest.mock import AsyncMock, patch, call

@pytest.mark.asyncio
async def test_planner_emits_approval_needed_event():
    state = build_initial_state("test-project", "task")
    
    mock_event_bus = AsyncMock()
    mock_event_bus.emit = AsyncMock()
    
    with patch("src.graph.nodes.planner.get_event_bus", return_value=mock_event_bus), \
         patch("src.graph.nodes.planner.manager_service.process_turn", 
               new_callable=AsyncMock,
               return_value={"summary": "Plan", "files": []}):
        
        result = await planner_node(state)
    
    # Event emit edildi mi?
    mock_event_bus.emit.assert_called_once()
    call_args = mock_event_bus.emit.call_args
    assert call_args[0][0] == "plan.approval_needed"
    assert "project_id" in call_args[0][1]

# Birden fazla emit kontrolü
@pytest.mark.asyncio
async def test_worker_emits_correct_events():
    mock_event_bus = AsyncMock()
    mock_event_bus.emit = AsyncMock()
    
    with patch("src.graph.nodes.worker.get_event_bus", return_value=mock_event_bus), \
         patch("src.core.llm_providers.generate_file_content",
               new_callable=AsyncMock,
               return_value=GeneratedFileContent(content="code", provider="stub", used_stub=True)):
        
        result = await worker_node(state_with_task)
    
    # Heartbeat ve done event'leri emit edilmeli
    emit_calls = [c[0][0] for c in mock_event_bus.emit.call_args_list]
    assert "system.heartbeat" in emit_calls
    assert "sprint.worker_done" in emit_calls
```

---

## References

- `pytest-async-test-skill/SKILL.md` — test yapısı
- `event-emission-pattern-skill/SKILL.md` — emit pattern
- `state-builder-for-tests-skill/SKILL.md` — test state
