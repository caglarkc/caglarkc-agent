---
name: graph-node-isolation-test
description: Coder AI için — LangGraph node fonksiyonlarını tüm graph çalıştırmadan izole birim testlerle doğrulama.
---

## Purpose

Her node'u bağımsız test ederek hataların tam kaynağını bulmayı sağlar.
Tüm graph'ı çalıştırmak yavaş ve bağımlıdır; node izolasyonu hızlı ve güvenilirdir.
Mock'larla dış bağımlılıkları keserek node mantığını test eder.

---

## When to Apply

- Yeni node implementasyonu yazıldığında
- Node'da hata ayıklanırken
- Node'un belirli bir input için doğru output ürettiği doğrulanırken

---

## Rules

- Node fonksiyonu direkt çağrılır: `result = await planner_node(state)`.
- Tüm dış bağımlılıklar (LLM, DB, event bus) mock'lanır.
- Test sadece node'un döndürdüğü dict'i doğrular.
- Graph compile edilmez, sadece node fonksiyonu test edilir.
- Side effect'ler (event emit, DB yazma) ayrıca doğrulanır.

---

## Guidelines

Node izolasyon test şablonu:
```python
# tests/test_nodes/test_planner_node.py
import pytest
from unittest.mock import AsyncMock, patch
from src.graph.nodes.planner import planner_node
from tests.helpers.state_builders import make_base_state


class TestPlannerNode:
    
    @pytest.mark.asyncio
    async def test_generates_draft_plan_on_execution_intent(self):
        state = make_base_state(task="planner'a retry ekle")
        
        mock_result = AsyncMock()
        mock_result.draft_plan = {"summary": "Retry ekle", "files": ["planner.py"]}
        mock_result.execution_intent = True
        mock_result.reply_text = "Plan hazır"
        
        with patch("src.graph.nodes.planner.manager_service.process_turn",
                   new_callable=AsyncMock, return_value=mock_result), \
             patch("src.graph.nodes.planner.get_event_bus") as mock_bus:
            
            mock_bus.return_value.emit = AsyncMock()
            result = await planner_node(state)
        
        # State güncellemelerini doğrula
        assert result.get("draft_plan") is not None
        assert result.get("approval_request") is not None
    
    @pytest.mark.asyncio
    async def test_returns_error_on_llm_failure(self):
        state = make_base_state()
        
        with patch("src.graph.nodes.planner.manager_service.process_turn",
                   new_callable=AsyncMock, side_effect=Exception("LLM down")):
            result = await planner_node(state)
        
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert result["errors"][0]["node"] == "planner"
    
    @pytest.mark.asyncio
    async def test_does_not_create_plan_for_discussion(self):
        state = make_base_state(task="nasıl yapılır?")
        
        mock_result = AsyncMock()
        mock_result.draft_plan = None
        mock_result.execution_intent = False
        mock_result.reply_text = "Şöyle yapılabilir..."
        
        with patch("src.graph.nodes.planner.manager_service.process_turn",
                   new_callable=AsyncMock, return_value=mock_result), \
             patch("src.graph.nodes.planner.get_event_bus") as mock_bus:
            mock_bus.return_value.emit = AsyncMock()
            result = await planner_node(state)
        
        assert result.get("draft_plan") is None
        assert result.get("approval_request") is None
```

---

## References

- `pytest-async-test-skill/SKILL.md` — test yapısı
- `mock-llm-response-skill/SKILL.md` — LLM mock
- `state-builder-for-tests-skill/SKILL.md` — test state
