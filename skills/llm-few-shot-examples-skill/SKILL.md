---
name: llm-few-shot-examples
description: Coder AI için — LLM prompt'una few-shot örnek eklemek; model davranışını örneklerle yönlendirmek.
---

## Purpose

Sıfır-shot prompt istenen formatı her zaman vermez.
Few-shot örnekler: "işte beklediğim giriş-çıkış" der, model yakınsar.
Özellikle JSON formatı veya spesifik kod stili için kritik.

---

## When to Apply

- Belirli bir çıktı formatı zorunluyken
- Model tutarsız yanıt verdiğinde
- Kod stili veya yapısı örnekle gösterilmek istendiğinde

---

## Rules

- Örnek sayısı: 2-3 yeterli (token tasarrufu).
- Örnekler: gerçek, geçerli giriş-çıkış çiftleri.
- Örnekler güncel tutulur — eski format örnekleri yanıltır.
- Örnekler prompt'un başına (system) veya ortasına eklenir.

---

## Guidelines

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

def build_few_shot_messages(
    examples: list[dict],
    task_input: str,
    system_prompt: str = "",
) -> list:
    """
    examples: [{"input": "...", "output": "..."}]
    """
    messages = []
    
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    
    for ex in examples:
        messages.append(HumanMessage(content=ex["input"]))
        messages.append(AIMessage(content=ex["output"]))
    
    messages.append(HumanMessage(content=task_input))
    return messages

# Örnek: JSON çıktı yönlendirme
TASK_PLAN_EXAMPLES = [
    {
        "input": "Hedef: Kullanıcı girişi ekle",
        "output": '{"tasks": [{"id": "t1", "description": "Login endpoint", "file_path": "src/auth/login.py", "estimated_minutes": 20}]}',
    },
    {
        "input": "Hedef: Loglama sistemi ekle",
        "output": '{"tasks": [{"id": "t1", "description": "Logger setup", "file_path": "src/utils/logger.py", "estimated_minutes": 15}]}',
    },
]

async def plan_with_examples(llm, goal: str) -> str:
    messages = build_few_shot_messages(
        examples=TASK_PLAN_EXAMPLES,
        task_input=f"Hedef: {goal}",
        system_prompt="Sprint hedefini görevlere böl. JSON formatında yanıt ver.",
    )
    response = await llm.ainvoke(messages)
    return response.content
```

---

## References

- `prompt-template-construction-skill/SKILL.md` — prompt şablonu
- `llm-prompt-chaining-skill/SKILL.md` — prompt zincirleme
- `llm-output-parsing-skill/SKILL.md` — çıktı ayrıştırma
