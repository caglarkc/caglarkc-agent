---
name: async-architecture-validation
description: Planner AI için — sistemin async mimarisinin tutarlı olduğunu doğrulamak; blocking call, yanlış await, event loop bloklaması gibi sorunları review sırasında tespit etmek.
---

## Purpose

Async/await tutarsızlıklarını review sırasında yakalar.
Blocking call tek bir yerde bile event loop'u dondurabilir.
Async mimarinin her katmanda doğru uygulandığını garantiler.

---

## When to Apply

- Her Coder AI kodu review'ında zorunlu kontrol
- Yeni I/O işlemi içeren kod geldiğinde
- Dış API çağrısı veya DB operasyonu review edilirken
- `asyncio` veya `await` içeren her dosyada

---

## Rules

- Her I/O operasyonu async olmalı: dosya, DB, HTTP, subprocess.
- `requests` yasak → `httpx.AsyncClient` kullanılmalı.
- `time.sleep()` yasak → `asyncio.sleep()`.
- `open()` yasak → `aiofiles.open()`.
- `sqlite3` yasak → `aiosqlite`.
- `asyncio.run()` sadece `main.py` entry point'te.
- `await` olmayan `async def` fonksiyon yazılmaz.

---

## Guidelines

Blocking call tespiti:
```python
# TESPİT EDİLECEK YASAKLAR:
import requests          # → httpx
import time; time.sleep  # → asyncio.sleep
import sqlite3           # → aiosqlite
open("file.txt")         # → aiofiles.open
subprocess.run()         # → asyncio.create_subprocess_exec

# DOĞRU KULLANIM:
async with httpx.AsyncClient() as client:
    resp = await client.get(url)

await asyncio.sleep(1)

async with aiosqlite.connect(db_path) as conn:
    await conn.execute(query)

async with aiofiles.open(path) as f:
    content = await f.read()
```

Yanlış async pattern:
```python
# YANLIŞ — await yok ama async var
async def get_config() -> dict:
    return {"key": "value"}  # I/O yok ama async — gereksiz, ama kabul edilebilir

# YANLIŞ — async olmayan context'te await
def sync_function():
    result = await some_async()  # SyntaxError
```

Event loop blokaj riski:
```python
# YANLIŞ — CPU-bound işlemi event loop'ta
async def heavy_compute():
    result = [i**2 for i in range(10_000_000)]  # event loop bloklar

# DOĞRU
async def heavy_compute():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: [i**2 for i in range(10_000_000)])
```

---

## References

- `python-async-patterns-skill/SKILL.md` — async pattern referansı
- `blocking-call-detection-skill/SKILL.md` — blocking tespit
- `code-mode-skill/SKILL.md` — coder async kuralları
