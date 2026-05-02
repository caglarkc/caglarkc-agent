---
name: structured-output-schema
description: Coder AI için — LangChain with_structured_output ile LLM'den doğrudan Pydantic modeli almak; JSON parse adımını ortadan kaldırmak.
---

## Purpose

Manuel JSON parse hatalı ve güvensiz.
`with_structured_output` LLM'i belirli şemaya göre yanıt vermeye zorlar.
Pydantic doğrulaması otomatik yapılır — ayrıca parse etme gerekmez.

---

## When to Apply

- Planner LLM'den yapılandırılmış plan çıktısı alınırken
- Worker görevi için şematik LLM yanıtı gerektiğinde
- LLM çıktısını JSON parse eden kod yazılırken

---

## Rules

- `with_structured_output(ModelClass)` tercih edilir manuel parse'a göre.
- Desteklemeyen model: `method="json_mode"` ile fallback.
- Strict mode: `strict=True` ile kesin şema uyumu.
- Model: Pydantic v2 `BaseModel`.

---

## Guidelines

```python
from pydantic import BaseModel, Field

class TaskSchema(BaseModel):
    task_id: str
    description: str
    files: list[str]
    depends_on: list[str] = Field(default_factory=list)

class SprintPlanSchema(BaseModel):
    tasks: list[TaskSchema]
    summary: str
    estimated_complexity: str = "medium"

# with_structured_output kullanımı
async def get_structured_plan(
    llm: BaseChatModel,
    messages: list,
) -> SprintPlanSchema:
    structured_llm = llm.with_structured_output(
        SprintPlanSchema,
        method="json_mode",  # veya "function_calling"
    )
    return await structured_llm.ainvoke(messages)

# Gemini için
async def get_gemini_plan(messages: list) -> SprintPlanSchema:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.gemini_api_key,
    )
    structured = llm.with_structured_output(SprintPlanSchema)
    return await structured.ainvoke(messages)

# Fallback: desteklenmiyor ise manuel parse
async def get_plan_with_fallback(
    llm: BaseChatModel,
    messages: list,
) -> SprintPlanSchema:
    try:
        return await get_structured_plan(llm, messages)
    except NotImplementedError:
        # Manuel parse fallback
        response = await llm.ainvoke(messages)
        return await parse_llm_json(response.content, SprintPlanSchema)
```

---

## References

- `llm-output-parsing-skill/SKILL.md` — manuel parse fallback
- `pydantic-v2-model-definition-skill/SKILL.md` — model tanımı
- `planner-node-implementation-skill/SKILL.md` — planner
