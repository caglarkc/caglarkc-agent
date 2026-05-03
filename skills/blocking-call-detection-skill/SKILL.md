---
name: blocking-call-detection
description: Coder AI için — async context'te event loop'u bloklayan sync çağrıları tespit etmek ve async alternatifleriyle değiştirmek.
---

## Purpose

Event loop'u bloklayan çağrılar tüm sistemi dondurabilir.
Özellikle LLM provider çağrısı, DB işlemi ve dosya I/O en yaygın blocking noktalarıdır.
Async alternatiflere geçiş tablosu ile hızlı düzeltme sağlar.

---

## When to Apply

- Her yeni I/O işlemi eklendiğinde
- Dış kütüphane entegre edildiğinde
- Performans sorunu araştırılırken
- Kod review sırasında import listesi kontrol edilirken

---

## Rules

- `requests` → `httpx.AsyncClient`
- `open()` → `aiofiles.open()`
- `sqlite3` → `aiosqlite`
- `time.sleep()` → `asyncio.sleep()`
- `subprocess.run()` → `asyncio.create_subprocess_exec()`
- CPU-bound işlemler → `loop.run_in_executor()`
- Sync kütüphane zorunluysa → `run_in_executor` ile thread pool'a taşı

---

## Guidelines

Blocking → Async dönüşüm tablosu:
```python
# HTTP
import requests  # BLOCKING
response = requests.get(url)  # BLOCKING
# →
import httpx
async with httpx.AsyncClient() as client:  # ASYNC
    response = await client.get(url)

# Dosya
with open("file.txt") as f:  # BLOCKING
    content = f.read()
# →
import aiofiles
async with aiofiles.open("file.txt") as f:  # ASYNC
    content = await f.read()

# DB
conn = sqlite3.connect(db_path)  # BLOCKING
cursor = conn.execute(query)
# →
async with aiosqlite.connect(db_path) as conn:  # ASYNC
    cursor = await conn.execute(query)

# Sleep
time.sleep(1)  # BLOCKING
# →
await asyncio.sleep(1)  # ASYNC

# CPU-bound
result = heavy_computation()  # BLOCKING event loop
# →
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, heavy_computation)  # ASYNC
```

Tespit aracı (import kontrolü):
```python
# Bu import'lar görülürse alarm ver:
import requests      # → httpx
import sqlite3       # → aiosqlite
import time         # time.sleep kullanılıyor mu?
from pathlib import Path  # Path.open() → aiofiles
```

---

## References

- `async-architecture-validation-skill/SKILL.md` — async doğrulama
- `run-in-executor-usage-skill/SKILL.md` — CPU-bound işlemler
- `python-async-patterns-skill/SKILL.md` — async referans
