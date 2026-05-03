---
name: asyncio-gather-usage
description: Coder AI için — birden fazla coroutine'i eş zamanlı çalıştırmak için asyncio.gather() kullanımının doğru yolu; exception handling ve return_exceptions.
---

## Purpose

Bağımsız async işlemleri paralel çalıştırarak sprint süresini kısaltır.
`return_exceptions=True` ile kısmi başarısızlık durumunda tüm sistem çökmez.
`gather` sonuçlarının doğru işlenmesini sağlar.

---

## When to Apply

- Birbirinden bağımsız birden fazla async işlem yapılırken
- Multiple worker'ı aynı anda başlatırken
- Paralel DB sorgular veya API çağrıları yapılırken

---

## Rules

- Bağımsız işlemler için `asyncio.gather()` zorunlu — sıralı `await` yasak.
- `return_exceptions=True` kullanılmalı (partial failure handling).
- Sonuçlar kontrol edilmeli: `isinstance(result, Exception)` ile.
- Task'lar bağımlıysa gather yerine sequential await kullanılır.
- Büyük sayıda task için semaphore ile rate limiting yapılır.

---

## Guidelines

Temel gather kullanımı:
```python
# DOĞRU — paralel
result_a, result_b, result_c = await asyncio.gather(
    service_a.process(),
    service_b.process(),
    service_c.process()
)

# YANLIŞ — sıralı (A ve B bağımsızsa verimsiz)
result_a = await service_a.process()
result_b = await service_b.process()
result_c = await service_c.process()
```

Exception handling ile gather:
```python
results = await asyncio.gather(
    worker_a.execute(task_a),
    worker_b.execute(task_b),
    worker_c.execute(task_c),
    return_exceptions=True
)

success_count = 0
for i, result in enumerate(results):
    if isinstance(result, Exception):
        logger.error(f"Worker {i} başarısız: {result}")
        # partial failure — diğerleri etkilenmedi
    else:
        success_count += 1
        logger.info(f"Worker {i} tamamlandı")

logger.info(f"{success_count}/3 worker başarılı")
```

Rate limiting ile gather:
```python
# Aynı anda maksimum 3 request
semaphore = asyncio.Semaphore(3)

async def limited_call(item: str) -> str:
    async with semaphore:
        return await api.call(item)

results = await asyncio.gather(*[limited_call(i) for i in items])
```

---

## References

- `asyncio-semaphore-usage-skill/SKILL.md` — rate limiting
- `parallel-task-identification-skill/SKILL.md` — paralel görev tespiti
- `worker-load-balancing-strategy-skill/SKILL.md` — worker dağılımı
