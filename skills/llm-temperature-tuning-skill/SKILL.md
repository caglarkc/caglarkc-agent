---
name: llm-temperature-tuning
description: Coder AI için — LLM temperature ayarını görev tipine göre doğru değere ayarlamak; kod üretimi için düşük, yaratıcı metin için yüksek temperature.
---

## Purpose

Temperature çok yüksek: kod tutarsız, syntax hatalı olur.
Temperature çok düşük: tek tip, yaratıcısız çıktı üretilir.
Doğru temperature göreve göre değişir.

---

## When to Apply

- LLM client oluşturulurken temperature ayarlanırken
- Planner vs worker için farklı temperature gerektiğinde
- LLM çıktı kalitesi düşükse temperature ayarı gözden geçirilirken

---

## Rules

- Kod üretimi (worker): `temperature=0.1` — deterministik.
- Plan oluşturma (planner): `temperature=0.2` — az yaratıcılık.
- Konuşma (PM): `temperature=0.3` — doğal yanıt.
- Review (reviewer): `temperature=0.1` — tutarlı analiz.
- `temperature=0.0`: tam deterministik, aynı input aynı çıktı.

---

## Guidelines

```python
# Görev tipine göre temperature
TEMPERATURE_BY_ROLE = {
    "planner":  0.2,   # Plan oluşturma — biraz esneklik
    "worker":   0.1,   # Kod üretimi — deterministik
    "reviewer": 0.1,   # Kod inceleme — tutarlı
    "chat":     0.3,   # Konuşma — doğal
}

def create_role_llm(
    role: str,
    settings: Settings,
) -> BaseChatModel:
    temperature = TEMPERATURE_BY_ROLE.get(role, 0.2)
    
    if role in ("planner", "reviewer", "chat"):
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=temperature,
        )
    else:  # worker
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=temperature,
        )

# Çalışma zamanında temperature override
async def invoke_with_temperature(
    llm: BaseChatModel,
    messages: list,
    temperature: float,
) -> BaseMessage:
    # Bazı modeller runtime override destekler
    if hasattr(llm, "temperature"):
        llm = llm.with_config({"temperature": temperature})
    return await llm.ainvoke(messages)
```

Temperature kılavuzu:
```
0.0  → Tam deterministik, test için ideal
0.1  → Kod üretimi
0.2  → Planlama
0.3  → Konuşma
0.7+ → Yaratıcı metin (kod için kullanılmaz)
```

---

## References

- `llm-provider-selection-skill/SKILL.md` — provider seçimi
- `prompt-template-construction-skill/SKILL.md` — prompt
- `worker-node-implementation-skill/SKILL.md` — worker
