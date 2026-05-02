---
name: abstract-base-class
description: Coder AI için — Python ABC (Abstract Base Class) ile interface sözleşmesi tanımlamak; implementasyonu olmayan abstract metod bildirmek.
---

## Purpose

ABC, alt sınıfların belirli metodları implement etmesini zorunlu kılar.
Eksik implementasyon: instantiation sırasında `TypeError` fırlatır.
`NotificationService`, `LLMProvider`, `Repository` gibi interface'ler için standart yaklaşım.

---

## When to Apply

- Birden fazla implementasyonu olacak interface tanımlanırken
- Plugin mimarisi kurulurken
- Test mock'ları için ortak interface belirlenirken

---

## Rules

- `from abc import ABC, abstractmethod` import edilir.
- Abstract metod: `@abstractmethod` dekoratörü.
- ABC'yi doğrudan instantiate etme — `TypeError` alırsın.
- `@property` abstract olabilir: `@property @abstractmethod`.
- Concrete alt sınıf tüm abstract metodları implement etmeli.

---

## Guidelines

```python
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """Storage backend interface."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Şema oluşturma, bağlantı kurma."""
        ...
    
    @abstractmethod
    async def get(self, key: str) -> dict | None:
        """Kayıt getir, yoksa None."""
        ...
    
    @abstractmethod
    async def put(self, key: str, value: dict) -> None:
        """Kayıt yaz veya güncelle."""
        ...
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Kayıt sil, bulunamazsa False."""
        ...
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Backend adı (sqlite, redis, memory)."""
        ...

class SQLiteBackend(StorageBackend):
    backend_name = "sqlite"
    
    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.executescript(CREATE_TABLES_SQL)
    
    async def get(self, key: str) -> dict | None: ...
    async def put(self, key: str, value: dict) -> None: ...
    async def delete(self, key: str) -> bool: ...

# ✗ Hata — abstract metod eksik
class IncompleteBackend(StorageBackend):
    backend_name = "broken"
    async def initialize(self) -> None: ...
    # get, put, delete eksik → TypeError
```

---

## References

- `notification-abstraction-skill/SKILL.md` — bildirim interface
- `plugin-architecture-skill/SKILL.md` — plugin sistemi
- `dependency-injection-patterns-skill/SKILL.md` — DI
