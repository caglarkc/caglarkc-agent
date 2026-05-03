---
name: worker-queue-overflow
description: Coder AI için — worker kuyruğu dolduğunda taşmayı yönetmek; yeni görevleri reddetmek veya bekletmek.
---

## Purpose

Sınırsız kuyruk bellek tüketir ve sistem çöker.
Overflow yönetimi: kuyruk doluysa yeni görev bekletilir veya reddedilir.
Back-pressure mekanizması sistemi kararlı tutar.

---

## When to Apply

- Worker kuyruğuna eleman eklenirken kapasite kontrol edilmesi gerektiğinde
- `MAX_QUEUE_SIZE` aşıldığında dispatcher uyarılırken
- Yüksek yük altında sistemin stabil kalması istendiğinde

---

## Rules

- Kuyruk maks: `MAX_QUEUE_SIZE = 100` (varsayılan).
- Overflow stratejisi: `backpressure` (beklet) veya `drop_oldest`.
- %80 dolulukta uyarı logu.
- %100 dolulukta: yeni ekleme bloklanır veya reddedilir.

---

## Guidelines

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

MAX_QUEUE_SIZE = 100
WARN_THRESHOLD = 0.8

class BoundedWorkerQueue:
    def __init__(self, maxsize: int = MAX_QUEUE_SIZE):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._maxsize = maxsize
    
    @property
    def size(self) -> int:
        return self._queue.qsize()
    
    @property
    def utilization(self) -> float:
        return self.size / self._maxsize
    
    async def put(self, item: dict, timeout: float = 5.0) -> bool:
        if self.utilization >= WARN_THRESHOLD:
            logger.warning(
                "Kuyruk %d%% dolu (%d/%d)",
                int(self.utilization * 100), self.size, self._maxsize,
            )
        try:
            await asyncio.wait_for(self._queue.put(item), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.error("Kuyruk dolu — görev reddedildi: %s", item.get("id"))
            return False
    
    async def get(self) -> dict:
        return await self._queue.get()
    
    def task_done(self) -> None:
        self._queue.task_done()
    
    async def drain(self) -> list[dict]:
        items = []
        while not self._queue.empty():
            items.append(self._queue.get_nowait())
        return items
```

---

## References

- `async-queue-usage-skill/SKILL.md` — async kuyruk kullanımı
- `worker-concurrency-control-skill/SKILL.md` — worker eşzamanlılık
- `dead-letter-queue-skill/SKILL.md` — başarısız görev kuyruğu
