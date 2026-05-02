---
name: batch-processing
description: Coder AI için — büyük listeyi küçük batch'lere bölerek işlemek; bellek kullanımını kontrol altında tutmak ve rate limit aşımını önlemek.
---

## Purpose

100 dosya tek seferde işlenmez — bellek ve rate limit sorunları çıkar.
Batch processing: N dosyayı işle, bitir, sonraki N'e geç.
Her batch arası bekleme rate limit'i önler.

---

## When to Apply

- Büyük dosya listesi paralel işlenirken
- LLM rate limit ile karşılaşıldığında
- Bellek sınırlı ortamda çalışırken

---

## Rules

- Batch boyutu: `MAX_CONCURRENT_WORKERS` (varsayılan 3).
- Batch arası bekleme: 1 saniye (rate limit buffer).
- Batch başarısızlığı: diğer batch'leri durdurmaz.
- İlerleme: her batch sonunda loglanır.

---

## Guidelines

```python
from typing import TypeVar, Callable, Awaitable

T = TypeVar("T")
R = TypeVar("R")

async def process_in_batches(
    items: list[T],
    processor: Callable[[T], Awaitable[R]],
    batch_size: int = 3,
    inter_batch_delay: float = 1.0,
) -> list[R | Exception]:
    results: list[R | Exception] = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(items) + batch_size - 1) // batch_size
        
        logger.info(f"Batch {batch_num}/{total_batches}: {len(batch)} öğe")
        
        batch_tasks = [processor(item) for item in batch]
        batch_results = await asyncio.gather(
            *batch_tasks,
            return_exceptions=True
        )
        results.extend(batch_results)
        
        # Son batch'ten sonra bekleme yok
        if i + batch_size < len(items):
            await asyncio.sleep(inter_batch_delay)
    
    return results

# Kullanım: Dosyaları batch ile işle
async def dispatch_files_in_batches(
    file_paths: list[str],
    state: OrchestratorState,
) -> None:
    async def process_file(path: str) -> dict:
        entry = build_queue_entry(...)
        return await worker_node(state, entry)
    
    results = await process_in_batches(
        file_paths,
        process_file,
        batch_size=3,
        inter_batch_delay=2.0,
    )
    
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        logger.error(f"{len(errors)} batch hatası")
```

---

## References

- `worker-concurrency-control-skill/SKILL.md` — eşzamanlılık
- `async-queue-usage-skill/SKILL.md` — kuyruk
- `rate-limit-handling-skill/SKILL.md` — rate limit
