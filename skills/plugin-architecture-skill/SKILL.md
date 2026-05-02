---
name: plugin-architecture
description: Coder AI için — yeni LLM provider, bildirim kanalı veya storage backend'i plugin olarak ekleyebilmek; genişletilebilir mimari tasarlamak.
---

## Purpose

Her yeni özellik core kod değiştirmeyi gerektirirse mimari kırılgandır.
Plugin sistemi yeni işlevselliği bağımsız modül olarak eklemeyi sağlar.
Interface'e uyan her implementasyon otomatik keşfedilir.

---

## When to Apply

- Yeni LLM provider eklenirken (core değiştirmeden)
- Notification kanalı genişletilirken
- Storage backend alternatifleri düşünülürken

---

## Rules

- Plugin: abstract base class'ı implement eder.
- Kayıt: merkezi registry veya `entry_points`.
- Plugin keşfi: import sırasında `__init_subclass__` veya explicit kayıt.
- Test: her plugin bağımsız test edilir.

---

## Guidelines

```python
from abc import ABC, abstractmethod

# Plugin interface
class LLMProvider(ABC):
    name: str  # sınıf değişkeni
    
    @abstractmethod
    async def ainvoke(self, messages: list) -> BaseMessage: ...
    
    @abstractmethod
    def is_available(self) -> bool: ...

# Plugin registry
class ProviderRegistry:
    _providers: dict[str, type[LLMProvider]] = {}
    
    @classmethod
    def register(cls, provider_class: type[LLMProvider]) -> None:
        cls._providers[provider_class.name] = provider_class
        logger.debug(f"Provider kayıtlı: {provider_class.name}")
    
    @classmethod
    def get(cls, name: str) -> type[LLMProvider] | None:
        return cls._providers.get(name)
    
    @classmethod
    def list_available(cls) -> list[str]:
        return [
            name for name, cls_ in cls._providers.items()
            if cls_().is_available()
        ]

# Plugin implementasyonu
class OllamaProvider(LLMProvider):
    name = "ollama"
    
    def __init__(self, settings: Settings):
        self._llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    
    async def ainvoke(self, messages: list) -> BaseMessage:
        return await self._llm.ainvoke(messages)
    
    def is_available(self) -> bool:
        return bool(settings.ollama_base_url)

# Kayıt
ProviderRegistry.register(OllamaProvider)
ProviderRegistry.register(GeminiProvider)
ProviderRegistry.register(OpenRouterProvider)
```

---

## References

- `provider-fallback-chain-skill/SKILL.md` — fallback
- `notification-abstraction-skill/SKILL.md` — bildirim soyutlama
- `dependency-injection-patterns-skill/SKILL.md` — DI
