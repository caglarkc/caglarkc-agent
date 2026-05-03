---
name: output-schema-validation
description: Coder AI için — LLM çıktısının beklenen JSON şemasına uygunluğunu doğrulamak; hatalı yapıyı erken yakalamak.
---

## Purpose

LLM bazen format dışı çıktı verir — eksik alan, yanlış tip, fazladan metin.
Şema doğrulama, bozuk çıktıyı validator node'da yakalar.
Erken hata, yanlış state güncellenmesini önler.

---

## When to Apply

- LLM'den JSON beklenen her yanıtta
- Executor node çıktıyı state'e yazmadan önce
- Validator node'da yapısal kontrol yapılırken

---

## Rules

- Şema: Pydantic v2 model veya TypedDict.
- Doğrulama başarısızsa: ham çıktı loglanır, retry tetiklenir.
- Kısmi doğrulama: zorunlu alanlar kontrol edilir, opsiyoneller görmezden gelinir.
- Şema değişikliği geriye dönük uyumlu tutulur.

---

## Guidelines

```python
import json
from pydantic import BaseModel, ValidationError
from typing import Any, Type, TypeVar

T = TypeVar("T", bound=BaseModel)

def validate_llm_output(
    raw_output: str,
    schema: Type[T],
    extract_json: bool = True,
) -> tuple[T | None, str | None]:
    """Returns (validated_model, error_message)"""
    text = raw_output
    if extract_json:
        text = _extract_json_block(raw_output)
    
    try:
        data = json.loads(text)
        model = schema.model_validate(data)
        return model, None
    except json.JSONDecodeError as e:
        return None, f"JSON parse hatası: {e}"
    except ValidationError as e:
        return None, f"Şema hatası: {e.error_count()} alan geçersiz"

def _extract_json_block(text: str) -> str:
    # Markdown kod bloğu varsa içini al
    if "```json" in text:
        start = text.index("```json") + 7
        end   = text.index("```", start)
        return text[start:end].strip()
    if "```" in text:
        start = text.index("```") + 3
        end   = text.index("```", start)
        return text[start:end].strip()
    # İlk { ... } bloğunu bul
    start = text.find("{")
    end   = text.rfind("}") + 1
    return text[start:end] if start != -1 else text

# Örnek şema
class TaskPlanOutput(BaseModel):
    tasks: list[dict]
    total_files: int
    estimated_minutes: float
```

---

## References

- `llm-output-parsing-skill/SKILL.md` — çıktı ayrıştırma
- `node-output-validation-skill/SKILL.md` — node çıktı doğrulama
- `structured-output-schema-skill/SKILL.md` — yapısal çıktı şeması
