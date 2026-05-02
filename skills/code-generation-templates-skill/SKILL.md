---
name: code-generation-templates
description: Coder AI için — tekrar eden kod kalıplarını (repository, service, node) şablon olarak tanımlamak; LLM'in ürettiği kodu standart yapıda tutmak.
---

## Purpose

Her repository sınıfı aynı yapıda olmalı — tutarsızlık bakımı zorlaştırır.
Şablonlar LLM prompt'una eklenerek standart üretim yapılır.
Yeni modül eklemek: şablonu doldur, özelleştir.

---

## When to Apply

- Worker node'da yeni repository, service veya node yazılırken
- LLM prompt'una kod yapısı örneği eklenmesi gerektiğinde
- Takım standartlarını zorunlu kılmak için

---

## Rules

- Şablonlar `src/templates/` altında tutulur.
- LLM prompt'a şablon + görev verilir.
- Şablon placeholder'ları: `{ClassName}`, `{model_name}`, `{table_name}`.
- Üretilen kod şablona uygunsa geçer; uygun değilse reviewer reddeder.

---

## Guidelines

Repository şablonu:
```python
REPOSITORY_TEMPLATE = '''
class {ClassName}Repository:
    """aiosqlite tabanlı {model_name} CRUD."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    async def create_{model_lower}(self, obj: {ClassName}) -> None:
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO {table_name} ({columns})
                VALUES ({placeholders})
            """, ({values}))
            await conn.commit()
    
    async def get_{model_lower}(self, id: str) -> {ClassName} | None:
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT * FROM {table_name} WHERE {pk} = ?", (id,)
            )
            row = await cursor.fetchone()
            return {ClassName}(**dict(row)) if row else None
    
    async def list_{model_lower}s(self) -> list[{ClassName}]:
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("SELECT * FROM {table_name}")
            rows = await cursor.fetchall()
            return [{ClassName}(**dict(row)) for row in rows]
'''
```

LLM prompt'a şablon ekleme:
```python
def build_repository_prompt(
    model_name: str,
    table_name: str,
    fields: list[str],
) -> list:
    return [
        SystemMessage(content="Aşağıdaki şablonu doldurarak repository yaz."),
        HumanMessage(content=(
            f"Model: {model_name}\nTablo: {table_name}\nAlanlar: {fields}\n\n"
            f"Şablon:\n{REPOSITORY_TEMPLATE}"
        )),
    ]
```

---

## References

- `prompt-template-construction-skill/SKILL.md` — prompt oluşturma
- `worker-node-implementation-skill/SKILL.md` — worker
- `aiosqlite-patterns-skill/SKILL.md` — DB pattern
