---
name: llm-tool-use-pattern
description: Coder AI için — LangChain/Anthropic tool use ile LLM'e araç tanımlamak; fonksiyon çağrısını yapılandırılmış olarak almak.
---

## Purpose

LLM düz metin yerine yapılandırılmış fonksiyon çağrısı yapabilir.
Tool use: araç tanımla → LLM uygun araçla yanıt verir → sonucu işle.
Kod üretimi yerine veri çıkarma ve eylem alma için güçlü yöntem.

---

## When to Apply

- LLM'den yapılandırılmış eylem alınmak istendiğinde
- Planner "görev oluştur" aracını çağırarak plan üretirken
- Arama, hesaplama gibi harici araç kullanımı gerektiğinde

---

## Rules

- Tool tanımı: Pydantic schema veya JSON Schema.
- Yanıt: `tool_calls` alanı kontrol edilir.
- Hata: LLM araç çağırmazsa prompt güçlendirilir.
- Paralel araç çağrısı: `tool_choice="any"` ile desteklenir.

---

## Guidelines

```python
from langchain_core.tools import tool
from pydantic import BaseModel

class CreateTaskInput(BaseModel):
    description:       str
    file_path:         str
    estimated_minutes: int
    priority:          int = 3

@tool(args_schema=CreateTaskInput)
def create_task(
    description: str,
    file_path: str,
    estimated_minutes: int,
    priority: int = 3,
) -> dict:
    """Yeni bir sprint görevi oluşturur."""
    import uuid
    return {
        "id":          str(uuid.uuid4())[:8],
        "description": description,
        "file_path":   file_path,
        "estimated_minutes": estimated_minutes,
        "priority":    priority,
        "status":      "planned",
    }

async def plan_with_tools(llm, goal: str) -> list[dict]:
    llm_with_tools = llm.bind_tools([create_task])
    response = await llm_with_tools.ainvoke(
        f"Bu hedef için görevler oluştur: {goal}"
    )

    tasks = []
    for call in response.tool_calls:
        if call["name"] == "create_task":
            task = create_task.invoke(call["args"])
            tasks.append(task)

    return tasks

# Anthropic API ile düşük seviye tool use
TASK_TOOL_SCHEMA = {
    "name":        "create_task",
    "description": "Sprint görevi oluşturur",
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "file_path":   {"type": "string"},
            "estimated_minutes": {"type": "integer"},
        },
        "required": ["description", "file_path", "estimated_minutes"],
    },
}
```

---

## References

- `llm-output-parsing-skill/SKILL.md` — çıktı ayrıştırma
- `structured-output-schema-skill/SKILL.md` — yapısal çıktı
- `llm-prompt-chaining-skill/SKILL.md` — prompt zincirleme
