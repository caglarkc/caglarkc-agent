---
name: caching-patterns
description: Coder AI için — sık erişilen verileri (proje bilgisi, şema) bellekte önbelleğe almak; gereksiz DB çağrısını azaltmak.
---

## Purpose

Aynı proje verisi her node çağrısında DB'den çekilirse yavaşlama olur.
In-memory cache sık kullanılan okuma sorgularını hızlandırır.
Cache invalidation: sprint tamamlandığında veya veri değiştiğinde.

---

## When to Apply

- Aynı `project_id` ile tekrarlanan sorgularda
- Statik yapılandırma verisi okunurken
- LLM çağrısı için prompt bağlamı birden fazla kez kurulurken

---

## Rules

- Cache: sadece read-only veriler için (proje, şema bilgisi).
- TTL: 5 dakika (kısa ömürlü — tutarlılık öncelikli).
- Mutasyondan sonra cache temizlenir.
- `functools.lru_cache` veya dict tabanlı basit cache.

---

## Guidelines

```python
import asyncio
from functools import lru_cache
from datetime import datetime, timedelta

class SimpleCache:
    def __init__(self, ttl_seconds: int = 300):
        self._store: dict[str, tuple[object, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, key: str) -> object | None:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if datetime.utcnow() > expires_at:
            del self._store[key]
            return None
        return value
    
    def set(self, key: str, value: object) -> None:
        self._store[key] = (value, datetime.utcnow() + self._ttl)
    
    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)
    
    def clear(self) -> None:
        self._store.clear()

# Repository'de kullanım
class CachingProjectRepository:
    def __init__(self, repo: ProjectRepository):
        self._repo = repo
        self._cache = SimpleCache(ttl_seconds=300)
    
    async def get_project(self, project_id: str) -> Project | None:
        cached = self._cache.get(f"project:{project_id}")
        if cached is not None:
            return cached
        
        project = await self._repo.get_project(project_id)
        if project:
            self._cache.set(f"project:{project_id}", project)
        return project
    
    async def update_project(self, project: Project) -> None:
        await self._repo.update_project(project)
        self._cache.invalidate(f"project:{project.project_id}")
```

---

## References

- `aiosqlite-patterns-skill/SKILL.md` — DB sorgulama
- `context-window-management-skill/SKILL.md` — bağlam yönetimi
- `dependency-injection-patterns-skill/SKILL.md` — DI
