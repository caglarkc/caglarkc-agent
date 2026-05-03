---
name: parametrize-test-cases
description: Coder AI için — pytest.mark.parametrize ile aynı test mantığını farklı input/output kombinasyonlarıyla çalıştırmak.
---

## Purpose

Aynı test 5 farklı girişle tekrar tekrar yazılırsa kod büyür.
`@pytest.mark.parametrize` ile tek test fonksiyonu, N farklı senaryoyu kapsar.
Edge case'ler parametre olarak kolayca eklenir.

---

## When to Apply

- Aynı fonksiyon birden fazla input değeri için test edilirken
- Geçerli/geçersiz input kombinasyonları test edilirken
- State machine geçişleri test edilirken

---

## Rules

- Her parametre seti: `(input, expected_output)` tuple.
- `ids` parametresi: okunabilir test ismi için.
- Async test: `@pytest.mark.asyncio` ile birlikte kullanılır.
- 10'dan fazla parametre varsa test verisi dosyaya alınır.

---

## Guidelines

```python
import pytest

# Basit parametrize
@pytest.mark.parametrize("status,expected_valid", [
    ("planned",     True),
    ("reserved",    True),
    ("in_progress", True),
    ("done",        True),
    ("failed",      True),
    ("invalid",     False),
    ("",            False),
    (None,          False),
])
def test_file_status_validation(status, expected_valid):
    result = is_valid_file_status(status)
    assert result == expected_valid

# Hata beklenen parametrize
@pytest.mark.parametrize("current,target,raises", [
    ("done",    "planned",     True),   # terminal'den geçiş yasak
    ("planned", "reserved",    False),  # geçerli
    ("failed",  "in_progress", True),   # geçersiz geçiş
], ids=["done_to_planned", "planned_to_reserved", "failed_to_inprogress"])
def test_file_state_transitions(current, target, raises):
    if raises:
        with pytest.raises(InvalidFileTransition):
            transition_file_status("test.py", {current: current}, target)
    else:
        result = transition_file_status("test.py", {"test.py": current}, target)
        assert result["test.py"] == target

# Async parametrize
@pytest.mark.asyncio
@pytest.mark.parametrize("provider_error,expected_fallback", [
    (TimeoutError, "openrouter"),
    (ConnectionError, "openrouter"),
])
async def test_provider_fallback(provider_error, expected_fallback, mock_llm):
    mock_llm.ainvoke.side_effect = provider_error
    result = await provider_chain.invoke_with_fallback(mock_input)
    assert result.provider == expected_fallback
```

---

## References

- `pytest-async-test-skill/SKILL.md` — async test
- `graph-node-isolation-test-skill/SKILL.md` — node testi
- `file-status-state-machine-skill/SKILL.md` — state machine
