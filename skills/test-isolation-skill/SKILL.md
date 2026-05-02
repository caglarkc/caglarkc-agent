---
name: test-isolation
description: Coder AI için — testlerin birbirinden bağımsız çalışmasını sağlamak; paylaşılan state, global singleton ve DB kalıntılarının testleri etkilemesini önlemek.
---

## Purpose

Bir test başarısız olduğunda diğeri de başarısız oluyorsa gerçek hata maskelenir.
Test izolasyonu: her test temiz state ile başlar.
Paralel test çalıştırma için gerekli.

---

## When to Apply

- Testler sıralı çalışınca geçip paralelde çalışınca başarısız oluyorsa
- Global singleton (EventBus) testlerde kirli state bırakıyorsa
- `tmp_path` yerine gerçek DB kullanılıyorsa

---

## Rules

- DB: her test `tmp_path` ile izole geçici dosya kullanır.
- EventBus: her test yeni instance alır (reset veya mock).
- Global state: `autouse` fixture ile test öncesi/sonrası temizlenir.
- `asyncio.Queue`: her test yeni queue alır.

---

## Guidelines

```python
# conftest.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock

@pytest_asyncio.fixture(autouse=True)
async def reset_event_bus():
    """Her test EventBus'u sıfırlar."""
    EventBus._instance = None   # singleton reset
    yield
    EventBus._instance = None

@pytest_asyncio.fixture
async def isolated_db(tmp_path):
    """Her test için izole DB."""
    db_path = str(tmp_path / "test.db")
    repo = ProjectRepository(db_path)
    await repo.initialize()
    yield repo
    # tmp_path pytest tarafından otomatik temizlenir

@pytest.fixture
def isolated_queue():
    """Her test için yeni kuyruk."""
    return asyncio.Queue()

# Test örneği
@pytest.mark.asyncio
async def test_worker_completes(isolated_db, isolated_queue):
    # Bu test başka testten etkilenmez
    entry = QueueEntry(...)
    await isolated_queue.put(entry)
    result = await process_queue(isolated_queue)
    assert result.success
```

Singleton reset pattern:
```python
class EventBus:
    _instance: "EventBus | None" = None
    
    @classmethod
    def reset(cls) -> None:
        """Test için singleton'ı sıfırla."""
        cls._instance = None
```

---

## References

- `pytest-async-test-skill/SKILL.md` — async test
- `fixture-factory-pattern-skill/SKILL.md` — fixture
- `mock-event-bus-skill/SKILL.md` — event bus mock
