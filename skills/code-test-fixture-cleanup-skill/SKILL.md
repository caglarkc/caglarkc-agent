---
name: code-test-fixture-cleanup
description: Coder AI için — test fixture'larının testlerden sonra temizlenmesini sağlamak; geçici dosya, DB kaydı ve mock'ların silinmesi.
---

## Purpose

Test sonrası artık dosya/veri birikmesi sonraki testleri kirletir.
Fixture cleanup: `yield` fixture veya `finalizer` ile otomatik temizlik.
Her test bağımsız, tekrarlanabilir olur.

---

## When to Apply

- DB kayıtları oluşturan test fixture'larında
- Geçici dosya veya dizin oluşturan testlerde
- Async mock veya patch uygulanan testlerde

---

## Rules

- Cleanup: `yield` fixture — setup/teardown tek fonksiyonda.
- Scope: mümkün olan en dar scope (function > class > module).
- Hata durumu: cleanup yine de çalışmalı (try/finally).
- Shared fixture: modül scope — dikkatli kullanım.

---

## Guidelines

```python
import pytest
import asyncio
from pathlib import Path
import tempfile

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
    # TemporaryDirectory context manager otomatik siler

@pytest.fixture
async def db_session(async_engine):
    async with async_engine.begin() as conn:
        yield conn
        await conn.rollback()  # Test sonrası geri al

@pytest.fixture
def mock_llm(monkeypatch):
    responses = []

    class MockLLM:
        async def ainvoke(self, messages):
            return type("Msg", (), {"content": responses.pop(0) if responses else ""})()

    llm = MockLLM()
    yield llm, responses
    # monkeypatch cleanup otomatik

@pytest.fixture
async def sprint_state():
    state = {
        "sprint_id":   "test_sprint_001",
        "sprint_goal": "Test goal",
        "tasks":       [],
        "file_registry": {},
    }
    yield state
    # Temizlik: state'e yazılan dosyaları sil
    for path in state.get("file_registry", {}):
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass

@pytest.fixture(scope="module")
def shared_db():
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    # Schema oluştur
    yield engine
    engine.dispose()  # Module scope: tüm testler bittikten sonra
```

---

## References

- `fixture-factory-pattern-skill/SKILL.md` — fixture fabrika
- `test-isolation-skill/SKILL.md` — test izolasyonu
- `mock-repository-pattern-skill/SKILL.md` — mock repository
