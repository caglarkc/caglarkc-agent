---
name: code-protocol-implementation
description: Coder AI için — Python Protocol sınıfları ile structural subtyping uygulamak; interface sözleşmesi olmadan duck typing güvenliğini sağlamak.
---

## Purpose

ABC (Abstract Base Class) kalıtım zorunda bırakır.
Protocol: kalıtım gerektirmez — duck typing'i statik olarak doğrular.
LLM, DB, notification gibi değiştirilebilir bileşenler için ideal.

---

## When to Apply

- Değiştirilebilir bileşen sözleşmesi tanımlanırken
- Test double (mock) oluşturulurken
- Harici bileşen bağımlılığı soyutlanırken

---

## Rules

- Protocol: sadece method imzaları — implement etmez.
- `runtime_checkable`: `isinstance()` ile kontrol gerekiyorsa.
- Implementasyon: Protocol'ü açıkça inherit etmek zorunda değil.
- Test: gerçek ve mock aynı Protocol'ü sağlar.

---

## Guidelines

```python
from typing import Protocol, runtime_checkable, AsyncIterator

@runtime_checkable
class LLMProvider(Protocol):
    async def ainvoke(self, messages: list) -> object: ...
    async def astream(self, messages: list) -> AsyncIterator[object]: ...

@runtime_checkable
class SprintRepository(Protocol):
    async def save_sprint(self, sprint: dict) -> None: ...
    async def load_sprint(self, sprint_id: str) -> dict | None: ...
    async def list_sprints(self, project_id: str) -> list[dict]: ...

@runtime_checkable
class Notifier(Protocol):
    async def send(self, message: str, channel: str = "default") -> bool: ...

# Protocol gereksinimleri karşılayan sınıf (inherit yok)
class GeminiProvider:
    async def ainvoke(self, messages: list) -> object:
        ...
    async def astream(self, messages: list):
        yield

# Tip kontrolü
def use_provider(provider: LLMProvider) -> None:
    assert isinstance(provider, LLMProvider), "LLMProvider protokolünü karşılamıyor"

# Test double
class MockLLM:
    def __init__(self, responses: list[str]):
        self._responses = iter(responses)

    async def ainvoke(self, messages: list) -> object:
        return type("M", (), {"content": next(self._responses, "")})()

    async def astream(self, messages: list):
        yield type("C", (), {"content": next(self._responses, "")})()
```

---

## References

- `abstract-base-class-skill/SKILL.md` — soyut temel sınıf
- `dependency-injection-patterns-skill/SKILL.md` — bağımlılık enjeksiyonu
- `mock-repository-pattern-skill/SKILL.md` — mock repository
