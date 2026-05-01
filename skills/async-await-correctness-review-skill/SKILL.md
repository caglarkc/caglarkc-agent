---
name: async-await-correctness-review
description: Planner AI için — await eksikliği, gereksiz async, yanlış event loop kullanımı gibi async/await hatalarını review sırasında tespit etmek.
---

## Purpose

Async/await yazım hatalarını review sırasında yakalar.
`await` unutulmuş coroutine çağrıları sessizce yanlış çalışır — yakalanması zordur.
Event loop blocking'i production'da ciddi performans sorununa yol açar.

---

## When to Apply

- Her async fonksiyon içeren kod review'ında zorunlu
- `async def` veya `await` geçen her dosyada

---

## Rules

- `async def` fonksiyon `await` içermiyorsa neden `async` olduğu sorgulanır.
- Coroutine çağrısı mutlaka `await` ile yapılmalı.
- `asyncio.run()` sadece main entry point'te kullanılır.
- `await asyncio.gather()` ile paralel çalıştırma, tek tek `await` değil.
- `async with` ve `async for` doğru kullanılmalı.
- Nested `asyncio.run()` çağrısı yasak (çalışmaz zaten).

---

## Guidelines

Yaygın hatalar:
```python
# HATA 1: await eksik — coroutine nesnesi döner, çalışmaz
result = some_async_func()  # ← await yok!
# DOĞRU:
result = await some_async_func()

# HATA 2: gereksiz async — I/O yok
async def get_project_name(project: dict) -> str:
    return project["name"]  # await yok, async gereksiz (zararsız ama temiz değil)

# HATA 3: asyncio.run() içinde asyncio.run()
async def outer():
    asyncio.run(inner())  # RuntimeError: event loop already running

# HATA 4: sıralı await yerine gather kullanılmamış
result_a = await task_a()  # sıralı
result_b = await task_b()  # sıralı — A ve B bağımsızsa verimsiz
# DOĞRU:
result_a, result_b = await asyncio.gather(task_a(), task_b())

# HATA 5: exception yakalanmadı gather içinde
results = await asyncio.gather(task_a(), task_b())  # task_a hata verirse crash
# DOĞRU:
results = await asyncio.gather(task_a(), task_b(), return_exceptions=True)
for r in results:
    if isinstance(r, Exception):
        logger.error(f"Task failed: {r}")
```

---

## References

- `async-architecture-validation-skill/SKILL.md` — genel async doğrulama
- `blocking-call-detection-skill/SKILL.md` — blocking call tespiti
- `python-async-patterns-skill/SKILL.md` — async referans
