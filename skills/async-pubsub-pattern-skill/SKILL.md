---
name: async-pubsub-pattern
description: Coder AI için — asyncio tabanlı pub/sub mesajlaşma deseni uygulamak; yayıncı ve abone bileşenleri gevşek bağlamak.
---

## Purpose

Doğrudan fonksiyon çağrısı tight coupling yaratır — değişim zor.
Pub/sub: yayıncı kimin dinlediğini bilmez, abone kimin yayımladığını bilmez.
Sistem genişlemesi: yeni abone eklemek mevcut kodu değiştirmez.

---

## When to Apply

- LangGraph node'ları arası dolaylı iletişim gerektiğinde
- Sprint event'leri birden fazla bileşene bildirilirken
- Test sırasında handler'ların izole test edilmesi istendiğinde

---

## Rules

- Topic isimleri: `{domain}.{event}` formatı (örn. `sprint.completed`).
- Wildcard abone: `sprint.*` tüm sprint event'lerini yakalar.
- Abone listesi: runtime'da değiştirilebilir.
- Bellek sızıntısı: abone kaldırılmazsa listener birikir.

---

## Guidelines

```python
import asyncio
import re
from collections import defaultdict
from typing import Awaitable, Callable

Handler = Callable[[str, dict], Awaitable[None]]

class PubSub:
    def __init__(self):
        self._exact:   dict[str, list[Handler]] = defaultdict(list)
        self._wildcard: list[tuple[re.Pattern, Handler]] = []
    
    def subscribe(self, pattern: str, handler: Handler) -> None:
        if "*" in pattern or "?" in pattern:
            regex = re.compile(pattern.replace(".", r"\.").replace("*", ".*"))
            self._wildcard.append((regex, handler))
        else:
            self._exact[pattern].append(handler)
    
    def unsubscribe(self, pattern: str, handler: Handler) -> None:
        if pattern in self._exact:
            self._exact[pattern] = [h for h in self._exact[pattern] if h is not handler]
    
    async def publish(self, topic: str, payload: dict) -> int:
        handlers: list[Handler] = list(self._exact.get(topic, []))
        for regex, h in self._wildcard:
            if regex.fullmatch(topic):
                handlers.append(h)
        
        if not handlers:
            return 0
        
        results = await asyncio.gather(
            *[h(topic, payload) for h in handlers],
            return_exceptions=True,
        )
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            import logging
            logging.getLogger(__name__).error("%d handler hatası", len(errors))
        
        return len(handlers) - len(errors)

# Kullanım
bus = PubSub()

async def log_all_sprint_events(topic: str, payload: dict) -> None:
    print(f"[{topic}] {payload}")

bus.subscribe("sprint.*", log_all_sprint_events)
```

---

## References

- `async-event-driven-skill/SKILL.md` — async event driven
- `message-bus-design-skill/SKILL.md` — mesaj otobüsü tasarımı
- `event-replay-skill/SKILL.md` — event tekrar oynatma
