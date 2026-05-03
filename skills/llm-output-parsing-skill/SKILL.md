---
name: llm-output-parsing
description: Coder AI için — LLM'den dönen ham metin veya JSON'ı güvenli şekilde parse etmek; bozuk çıktıyı tolere etmek.
---

## Purpose

LLM her zaman geçerli JSON döndürmez — bazen markdown fence içine sarar, bazen trailing comma ekler.
Robust parse mantığı bu varyasyonları tolere eder.
Parse başarısız olursa retry veya fallback devreye girer.

---

## When to Apply

- Planner node'da LLM plan çıktısı alınırken
- Worker node'da LLM kod çıktısı işlenirken
- Structured output için `with_structured_output` kullanılamadığında

---

## Rules

- JSON bekliyorsan: önce markdown fence temizle, sonra parse et.
- `json.loads` başarısız olursa: `json5` veya regex fallback dene.
- Parse tamamen başarısız: ham çıktıyı logla, `LLMParseError` fırlat.
- Pydantic ile doğrula — sadece JSON olmakla yetinme.
- LLM çıktısını asla doğrudan `eval()` etme.

---

## Guidelines

```python
import json
import re

class LLMParseError(Exception):
    pass

def extract_json_from_response(text: str) -> str:
    """Markdown fence içindeki JSON'ı çıkarır."""
    # ```json ... ``` veya ``` ... ``` bloklarını temizle
    fence_match = re.search(
        r'```(?:json)?\s*\n?(.*?)\n?```',
        text,
        re.DOTALL
    )
    if fence_match:
        return fence_match.group(1).strip()
    
    # JSON nesnesi veya dizisi bul
    obj_match = re.search(r'\{.*\}', text, re.DOTALL)
    if obj_match:
        return obj_match.group(0)
    
    arr_match = re.search(r'\[.*\]', text, re.DOTALL)
    if arr_match:
        return arr_match.group(0)
    
    return text.strip()

async def parse_llm_json(
    raw: str,
    model_class: type[BaseModel]
) -> BaseModel:
    cleaned = extract_json_from_response(raw)
    
    try:
        data = json.loads(cleaned)
        return model_class.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f"LLM parse hatası: {e}\nHam: {raw[:200]}")
        raise LLMParseError(f"LLM çıktısı parse edilemedi: {e}") from e
```

`with_structured_output` kullanımı (tercihli):
```python
structured_llm = llm.with_structured_output(LLMPlanOutput)
result: LLMPlanOutput = await structured_llm.ainvoke(messages)
```

---

## References

- `input-validation-patterns-skill/SKILL.md` — Pydantic doğrulama
- `planner-node-implementation-skill/SKILL.md` — planner
- `retry-decorator-implementation-skill/SKILL.md` — retry
