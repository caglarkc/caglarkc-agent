---
name: async-queue-usage
description: Coder AI için — asyncio.Queue ile dispatcher ve worker arasında iş kuyruğu oluşturmak; producer/consumer pattern uygulamak.
---

## Purpose

Dispatcher dosya işlerini kuyruğa koyar; worker'lar kuyruktan çeker.
`asyncio.Queue` thread-safe ve async — ideal producer/consumer.
`maxsize` ile kuyruk dolu olduğunda backpressure uygulanır.

---

## When to Apply

- Dispatcher worker'a iş gönderirken
- Paralel worker'lar tek kuyruktan beslenmesi gerektiğinde
- Backpressure mekanizması uygulanırken

---

## Rules

- `maxsize=0`: sınırsız kuyruk (dikkatli kullanılır).
- `maxsize=N`: N dolduğunda `put()` bloklanır — backpressure sağlar.
- `task_done()` her `get()` sonrası çağrılmalı — `join()` için gerekli.
- Worker exception'ı kuyruktan çıkan item'ı tekrar koymamalı (dead loop riski).
- Shutdown: sentinel değer (`None`) ile worker'lar durdurulur.

---

## Guidelines

```python
import asyncio
from typing import Optional

SENTINEL = None  # kuyruk bitiş sinyali

async def dispatcher_producer(
    queue: asyncio.Queue,
    entries: list[QueueEntry]
) -> None:
    for entry in entries:
        await queue.put(entry)
        logger.debug(f"Kuyruğa eklendi: {entry.file_path}")
    
    # Worker sayısı kadar sentinel ekle
    for _ in range(MAX_CONCURRENT_WORKERS):
        await queue.put(SENTINEL)

async def worker_consumer(
    worker_id: str,
    queue: asyncio.Queue,
    results: list
) -> None:
    while True:
        item = await queue.get()
        
        if item is SENTINEL:
            queue.task_done()
            break
        
        try:
            result = await process_queue_entry(item)
            results.append(result)
        except Exception as e:
            logger.error(f"Worker {worker_id} hata: {item.file_path}: {e}")
        finally:
            queue.task_done()

async def run_parallel_workers(entries: list[QueueEntry]) -> list:
    queue: asyncio.Queue[Optional[QueueEntry]] = asyncio.Queue(maxsize=10)
    results = []
    
    # Producer + consumer'ları eş zamanlı başlat
    producer = asyncio.create_task(dispatcher_producer(queue, entries))
    consumers = [
        asyncio.create_task(worker_consumer(f"w{i}", queue, results))
        for i in range(MAX_CONCURRENT_WORKERS)
    ]
    
    await asyncio.gather(producer, *consumers)
    return results
```

---

## References

- `queue-entry-construction-skill/SKILL.md` — kuyruk girişi
- `worker-status-tracking-skill/SKILL.md` — worker takibi
- `asyncio-task-creation-skill/SKILL.md` — task oluşturma
