---
name: type-narrowing-patterns
description: Coder AI için — Python type system'inde tür daraltma (type narrowing) kalıplarını uygulamak; mypy uyumlu kod yazmak.
---

## Purpose

`dict | None` türünde `None` kontrolü yapılmazsa mypy hata verir.
Type narrowing: koşullu kontrol sonrası türü daraltır, static analyzer anlar.
Güvenli kod + IDE otomatik tamamlama + tip hatası olmadan çalışma.

---

## When to Apply

- `Optional` veya `Union` türleri kullanılırken
- `isinstance()` kontrolü gerektiren kod yazılırken
- mypy veya pyright ile type check yapılırken

---

## Rules

- `Optional[X]` yerine `X | None` (Python 3.10+).
- None kontrolü: `if x is not None:` sonrasında `x` narrowed olur.
- `isinstance()`: discriminated union için kullanılır.
- `TypeGuard`: özel narrowing fonksiyonları için.

---

## Guidelines

```python
from typing import TypeGuard

# 1. None check narrowing
def process(value: str | None) -> str:
    if value is None:
        return ""
    # Burada value: str (narrowed)
    return value.upper()

# 2. isinstance narrowing
def handle_result(result: dict | list | str) -> str:
    if isinstance(result, dict):
        return str(result.get("content", ""))
    elif isinstance(result, list):
        return ", ".join(str(x) for x in result)
    # Burada result: str (narrowed)
    return result

# 3. TypeGuard ile özel narrowing
def is_task_dict(obj: object) -> TypeGuard[dict[str, str]]:
    return (
        isinstance(obj, dict)
        and "id" in obj
        and "status" in obj
    )

def process_task(raw: object) -> None:
    if is_task_dict(raw):
        # raw: dict[str, str] (narrowed)
        print(raw["id"])

# 4. Discriminated union
from dataclasses import dataclass
from typing import Literal

@dataclass
class SuccessResult:
    kind: Literal["success"]
    data: str

@dataclass
class ErrorResult:
    kind: Literal["error"]
    message: str

Result = SuccessResult | ErrorResult

def handle(r: Result) -> str:
    if r.kind == "success":
        return r.data   # r: SuccessResult
    return f"Hata: {r.message}"  # r: ErrorResult
```

---

## References

- `type-alias-definition-skill/SKILL.md` — tip takma adı
- `dataclass-vs-pydantic-skill/SKILL.md` — dataclass vs pydantic
- `input-validation-patterns-skill/SKILL.md` — giriş doğrulama
