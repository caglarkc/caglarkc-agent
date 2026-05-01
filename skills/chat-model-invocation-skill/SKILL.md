---
name: chat-model-invocation
description: Coder AI için — LangChain ChatModel (Gemini, OpenRouter) ile doğru async çağrı yapma; mesaj listesi oluşturma, structured output ve hata yönetimi.
---

## Purpose

LLM çağrısının bu projede nasıl yapılacağını standartlaştırır.
Gemini, OpenRouter ve Ollama için tutarlı invocation pattern sağlar.
Structured output parsing ve fallback zincirini uygular.

---

## When to Apply

- `src/core/manager_planning.py` veya `src/core/llm_providers.py` için LLM çağrısı yazılırken
- Yeni LLM entegrasyonu eklenirken
- Prompt şablonu oluşturulurken

---

## Rules

- `ainvoke()` async çağrısı zorunlu — `invoke()` yasak.
- Mesaj listesi: `[SystemMessage(...), HumanMessage(...)]` formatı.
- Structured output: `model.with_structured_output(PydanticModel)` tercih edilir.
- Timeout: `httpx` veya model konfigürasyonunda 30 saniye.
- Fallback: `model.with_fallbacks([backup_model])` zinciri.
- API key `settings` üzerinden, hardcode yasak.

---

## Guidelines

Gemini chat model:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def build_gemini_model() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key.get_secret_value(),
        temperature=0.1,
        timeout=30
    )
```

Structured output ile çağrı:
```python
from pydantic import BaseModel

class PlanOutput(BaseModel):
    summary: str
    files: list[str]
    dependencies: dict[str, list[str]]
    execution_intent: bool

model = build_gemini_model()
structured_model = model.with_structured_output(PlanOutput)

messages = [
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=user_message)
]

result: PlanOutput = await structured_model.ainvoke(messages)
```

Fallback zinciri:
```python
primary = build_gemini_model()
fallback = build_openrouter_model()

model_with_fallback = primary.with_fallbacks(
    [fallback],
    exceptions_to_handle=(Exception,)
)
result = await model_with_fallback.ainvoke(messages)
```

JSON output (structured output yetersizse):
```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
chain = model | parser
result = await chain.ainvoke(messages)
```

---

## References

- `provider-fallback-chain-skill/SKILL.md` — provider zinciri
- `prompt-construction-pattern-skill/SKILL.md` — prompt yapısı
- `structured-output-parsing-skill/SKILL.md` — output parsing
