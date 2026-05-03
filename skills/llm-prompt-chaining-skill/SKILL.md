---
name: llm-prompt-chaining
description: Coder AI için — birden fazla LLM çağrısını zincirlemek; bir çağrının çıktısını sonrakinin girdisi olarak kullanmak.
---

## Purpose

Tek prompt karmaşık görevi yeterince çözemeyebilir.
Zincirleme: analiz → planlama → üretim adımlarını ayrı çağrılara böler.
Her adım daha odaklı, çıktı kalitesi artar.

---

## When to Apply

- Kod üretimi önce analiz gerektirdiğinde
- Büyük görev alt adımlara bölündüğünde
- Bir LLM çıktısı doğrulama için başka LLM'e gönderildiğinde

---

## Rules

- Her zincir halkası bağımsız LLM çağrısıdır.
- Önceki çıktı bir sonraki prompt'a eklenir (context injection).
- Zincir 5 adımı geçmemeli — token maliyeti artar.
- Hata: hangi adımda koptuğu loglanır.

---

## Guidelines

```python
from langchain_core.messages import HumanMessage, SystemMessage

async def prompt_chain(
    llm,
    steps: list[dict],  # [{"system": ..., "user_template": ..., "input_key": ...}]
    initial_input: str,
) -> list[str]:
    results = []
    current_input = initial_input
    
    for i, step in enumerate(steps):
        user_msg = step["user_template"].format(input=current_input)
        messages = [
            SystemMessage(content=step.get("system", "")),
            HumanMessage(content=user_msg),
        ]
        response = await llm.ainvoke(messages)
        result = response.content
        results.append(result)
        current_input = result  # Bir sonraki adıma geçir
    
    return results

# Örnek zincir: analiz → plan → kod
CODE_GEN_CHAIN = [
    {
        "system": "Sen bir Python mimarısın.",
        "user_template": "Şu görevi analiz et: {input}\nGereksinimler ve bağımlılıklar nelerdir?",
    },
    {
        "system": "Sen bir yazılım planlayıcısısın.",
        "user_template": "Bu analize göre uygulama planı yap:\n{input}",
    },
    {
        "system": "Sen bir Python yazılımcısısın.",
        "user_template": "Bu plana göre kodu yaz:\n{input}",
    },
]
```

---

## References

- `prompt-template-construction-skill/SKILL.md` — prompt şablonu
- `context-injection-strategy-skill/SKILL.md` — bağlam enjeksiyonu
- `llm-output-parsing-skill/SKILL.md` — çıktı ayrıştırma
