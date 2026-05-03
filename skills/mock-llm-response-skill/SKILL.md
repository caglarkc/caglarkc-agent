---
name: mock-llm-response
description: Coder AI için — test sırasında gerçek LLM API çağrısı yapmadan sahte yanıt döndürmek; AsyncMock ile provider mock'lama.
---

## Purpose

Testlerin gerçek LLM API'sına bağımlı olmamasını sağlar.
API key olmadan, internet bağlantısı olmadan test çalışır.
LLM yanıtını kontrol ederek belirli senaryoları test etmeyi sağlar.

---

## When to Apply

- LLM çağrısı içeren node veya servis test edilirken
- Provider fallback zinciri test edilirken
- Spesifik LLM yanıt formatını test ederken

---

## Rules

- `unittest.mock.AsyncMock` kullanılır (sync Mock değil).
- Mock'lama hedef: çağrılan fonksiyon veya method.
- `side_effect` ile exception simülasyonu.
- `return_value` ile başarılı yanıt simülasyonu.
- Mock'lar test sonrası otomatik temizlenir (`with patch`).

---

## Guidelines

LLM provider mock'lama:
```python
from unittest.mock import AsyncMock, patch, MagicMock

# Gemini model mock
@pytest.mark.asyncio
async def test_manager_planning_success():
    mock_response = MagicMock()
    mock_response.content = '{"summary": "Plan", "files": ["a.py"], "execution_intent": true}'
    
    with patch(
        "src.core.manager_planning.ChatGoogleGenerativeAI",
    ) as MockGemini:
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=mock_response)
        MockGemini.return_value = mock_model
        
        service = ManagerPlanningService()
        result = await service.process_turn("retry ekle", [])
    
    assert result.execution_intent is True

# LLM provider fonksiyon mock
@pytest.mark.asyncio
async def test_generate_file_content_fallback():
    with patch(
        "src.core.llm_providers._call_ollama",
        new_callable=AsyncMock,
        side_effect=ProviderConnectionError("Ollama çalışmıyor")
    ), patch(
        "src.core.llm_providers._call_openrouter_primary",
        new_callable=AsyncMock,
        return_value="# Generated code"
    ):
        result = await generate_file_content(
            "worker_a",
            {"target_file": "test.py", "description": "test"},
            "context"
        )
    
    assert result.provider == "openrouter_primary"
    assert result.used_stub is False
```

Stub fallback test:
```python
@pytest.mark.asyncio
async def test_all_providers_fail_returns_stub():
    with patch("src.core.llm_providers._call_ollama", side_effect=Exception("down")), \
         patch("src.core.llm_providers._call_openrouter_primary", side_effect=Exception("down")), \
         patch("src.core.llm_providers._call_openrouter_secondary", side_effect=Exception("down")):
        
        result = await generate_file_content("worker_a", task, "context")
    
    assert result.used_stub is True
    assert result.provider == "stub"
```

---

## References

- `pytest-async-test-skill/SKILL.md` — test yapısı
- `provider-fallback-chain-skill/SKILL.md` — fallback zinciri
- `graph-node-isolation-test-skill/SKILL.md` — node izolasyonu
