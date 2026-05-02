---
name: sentinel-value-pattern
description: Coder AI için — None ile ayırt edilemeyen "değer yok" durumları için sentinel nesneleri tanımlamak; Optional'ın yetersiz kaldığı durumlarda kullanmak.
---

## Purpose

`None` hem "değer yok" hem de "geçerli değer olarak None" anlamına gelebilir.
Sentinel nesne bu belirsizliği kaldırır.
`Queue` kapanışı veya "henüz ayarlanmadı" durumları için yaygın kullanılır.

---

## When to Apply

- `asyncio.Queue`'ya kapanış sinyali gönderilirken
- Optional parametrenin "verilmedi" ile "None verildi" arasında ayırım gerektiğinde
- Default değer tanımlanmadan önce "değer set edildi mi?" kontrolü yapılırken

---

## Rules

- Sentinel: modül düzeyinde `object()` ile tanımlanır.
- Tip annotation: `Sentinel = object; _MISSING: Sentinel = Sentinel()`.
- Python 3.13+: `enum.MISSING` veya `typing.NoDefault` kullanılabilir.
- `is` ile karşılaştırılır — `==` değil.

---

## Guidelines

```python
# Modül düzeyinde sentinel
_MISSING = object()   # "değer sağlanmadı" sentinel

def get_setting(
    key: str,
    default=_MISSING,
) -> str:
    value = os.environ.get(key)
    if value is None:
        if default is _MISSING:
            raise KeyError(f"Zorunlu ayar eksik: {key}")
        return default
    return value

# Queue kapanış sentinel'i (typed)
from typing import TypeVar, Generic

T = TypeVar("T")
_QueueSentinel = object()
QUEUE_DONE: object = _QueueSentinel  # tip denetimi için

async def worker_consume(queue: asyncio.Queue) -> None:
    while True:
        item = await queue.get()
        if item is QUEUE_DONE:
            queue.task_done()
            return
        await process(item)
        queue.task_done()

# Eski Python uyumlu sentinel class
class _MissingType:
    def __repr__(self) -> str:
        return "MISSING"
    
    def __bool__(self) -> bool:
        return False

MISSING = _MissingType()
```

---

## References

- `async-queue-usage-skill/SKILL.md` — kuyruk kapanış
- `input-validation-patterns-skill/SKILL.md` — parametre doğrulama
- `type-alias-definition-skill/SKILL.md` — tip alias
