---
name: llm-provider-selection
description: Planner AI için — Gemini, Ollama veya OpenRouter arasında hangi provider'ın hangi görev için kullanılacağına karar vermek.
---

## Purpose

Her provider'ın avantajları farklı — doğru seçim hem kalite hem maliyet etkiler.
Planner Gemini kullanır (akıl yürütme); Coder Ollama kullanır (kod üretme).
Provider seçimi konfigürasyona bağlıdır — hard-code edilmez.

---

## When to Apply

- Hangi node'un hangi LLM'i kullanacağına karar verilirken
- Settings'te LLM konfigürasyonu yapılırken
- Provider değiştirme gerektiğinde

---

## Rules

- **Planner/Reviewer**: Gemini 2.5 Flash — güçlü akıl yürütme.
- **Worker (Coder)**: Ollama codellama:13b — yerel, maliyet yok.
- **Fallback**: Ollama çalışmıyorsa OpenRouter.
- Provider seçimi `Settings` üzerinden yapılır.
- LLM instance dependency injection ile node'lara verilir.

---

## Guidelines

```python
# src/core/llm_factory.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

def create_planner_llm(settings: Settings) -> BaseChatModel:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.gemini_api_key,
        temperature=0.2,
    )

def create_coder_llm(settings: Settings) -> BaseChatModel:
    if settings.ollama_base_url:
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.1,
        )
    
    if settings.openrouter_api_key:
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            model="deepseek/deepseek-coder",
        )
    
    raise ValueError("Hiçbir coder LLM provider konfigüre edilmedi")
```

Provider karşılaştırma:
```
Gemini 2.5 Flash:  akıl yürütme ✓, kod ✓, hız ✓, maliyet $$
Ollama codellama:  kod ✓, yerel ✓, maliyet yok, offline ✓
OpenRouter:        model seçimi ✓, fallback ✓, maliyet $
```

---

## References

- `provider-fallback-chain-skill/SKILL.md` — fallback
- `settings-validation-skill/SKILL.md` — config
- `dependency-injection-patterns-skill/SKILL.md` — DI
