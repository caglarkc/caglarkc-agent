---
name: async-generator-pattern
description: Coder AI için — async generator (async def + yield) kullanarak büyük veri setlerini bellek verimli şekilde akış halinde işlemek.
---

## Purpose

Tüm veritabanı kayıtlarını belleğe yükleme gerekebilir.
`async for` ile async generator sadece ihtiyaç duyulduğunda yükler.
Büyük sprint geçmişi, log satırları için ideal.

---

## When to Apply

- Büyük liste DB'den sayfalama ile çekilirken
- Log dosyası satır satır işlenirken
- Streaming LLM yanıtı işlenirken

---

## Rules

- `async def` + `yield`: async generator tanımı.
- `async for`: tüketim.
- Generator içinde exception: `try/finally` ile kaynak temizlenir.
- `return` kullanılmaz — `StopAsyncIteration` otomatik.

---

## Guidelines

```python
from typing import AsyncGenerator

# DB'den sayfalama
async def iter_sprints(
    db_path: str,
    project_id: str,
    page_size: int = 100
) -> AsyncGenerator[Sprint, None]:
    offset = 0
    async with aiosqlite.connect(db_path) as conn:
        while True:
            cursor = await conn.execute(
                "SELECT * FROM sprints WHERE project_id = ? "
                "ORDER BY created_at LIMIT ? OFFSET ?",
                (project_id, page_size, offset)
            )
            rows = await cursor.fetchall()
            if not rows:
                return
            for row in rows:
                yield Sprint(**dict(row))
            offset += page_size

# Streaming LLM yanıtı
async def stream_llm_response(
    llm: BaseChatModel,
    messages: list,
) -> AsyncGenerator[str, None]:
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield chunk.content

# Tüketim
async def process_all_sprints(project_id: str) -> None:
    async for sprint in iter_sprints(settings.db_path, project_id):
        await process_sprint(sprint)

# Streaming çıktı
full_response = ""
async for token in stream_llm_response(llm, messages):
    print(token, end="", flush=True)
    full_response += token
```

---

## References

- `aiosqlite-patterns-skill/SKILL.md` — DB sorgulama
- `async-context-manager-skill/SKILL.md` — kaynak yönetimi
- `async-function-template-skill/SKILL.md` — async pattern
