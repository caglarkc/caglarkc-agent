---
name: model-fallback-chain
description: Coder AI için — birincil LLM model başarısız olduğunda yedek modellere sırayla geçiş yapmak.
---

## Purpose

Tek model bağımlılığı: model çöktüğünde sistem durur.
Fallback zinciri: Gemini → OpenRouter → Ollama → Stub sırasıyla dener.
Her geçiş loglanır, kullanıcı bilgilendirilir.

---

## When to Apply

- LLM çağrısı `RateLimitError` veya `TimeoutError` verdiğinde
- Provider API yanıt vermediğinde
- Kritik işlem yedek modelle tamamlanabilirken

---

## Rules

- Zincir: en yetenekliden en basiteye doğru.
- Her model için retry: 2 deneme.
- Stub (son çare): sabit yanıt, üretim kullanımı yok.
- Fallback geçişi: state'e kaydedilir, izlenebilir.

---

## Guidelines

```python
from typing import Protocol

class LLMProvider(Protocol):
    async def ainvoke(self, messages: list) -> object: ...

async def invoke_with_fallback(
    providers: list[tuple[str, LLMProvider]],
    messages: list,
    logger=None,
) -> tuple[object, str]:
    last_error = None
    
    for provider_name, provider in providers:
        for attempt in range(1, 3):
            try:
                result = await provider.ainvoke(messages)
                if logger:
                    logger.info("Provider kullanıldı: %s", provider_name)
                return result, provider_name
            except Exception as exc:
                last_error = exc
                if logger:
                    logger.warning(
                        "[%s] attempt %d başarısız: %s",
                        provider_name, attempt, exc,
                    )
    
    raise RuntimeError(f"Tüm provider'lar başarısız. Son hata: {last_error}")

# Provider zinciri kurulumu
def build_provider_chain(config: dict) -> list[tuple[str, LLMProvider]]:
    chain = []
    
    if config.get("gemini_api_key"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        chain.append(("gemini", ChatGoogleGenerativeAI(model="gemini-2.0-flash")))
    
    if config.get("openrouter_api_key"):
        from langchain_openai import ChatOpenAI
        chain.append(("openrouter", ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config["openrouter_api_key"],
            model="mistralai/mistral-7b-instruct",
        )))
    
    # Ollama — yerel, her zaman dene
    try:
        from langchain_ollama import ChatOllama
        chain.append(("ollama", ChatOllama(model="llama3.2")))
    except ImportError:
        pass
    
    return chain
```

---

## References

- `llm-provider-selection-skill/SKILL.md` — provider seçimi
- `retry-decision-logic-skill/SKILL.md` — retry kararı
- `graceful-degradation-skill/SKILL.md` — zarif bozulma
