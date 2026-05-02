---
name: sprint-template-library
description: Planner AI için — sık tekrar eden sprint türleri için hazır şablonlar bulundurmak; "repository katmanı ekle" gibi istekleri şablondan hızla planlamak.
---

## Purpose

Her "yeni repository ekle" isteğinde aynı görev listesi üretilir.
Şablon kütüphanesi bu tekrarı ortadan kaldırır.
LLM'den daha hızlı ve tutarlı plan üretilir.

---

## When to Apply

- Kullanıcı isteği bilinen bir pattern'e uyduğunda
- LLM'e gidilmeden hızlı plan üretilmek istendiğinde
- Sprint türü: CRUD, entegrasyon, test, refactor

---

## Rules

- Şablon: görev ve dosya listesinin placeholder versiyonu.
- Placeholder: `{model_name}`, `{table_name}`, `{module}` vb.
- Şablon eşleştirme: kullanıcı mesajındaki anahtar kelimelerle.
- Şablon bulunamazsa: LLM'e fallback.

---

## Guidelines

```python
SPRINT_TEMPLATES = {
    "crud_repository": {
        "name": "CRUD Repository",
        "triggers": ["repository ekle", "crud", "veritabanı katmanı"],
        "tasks": [
            {
                "description": "{ModelName} modeli tanımla",
                "files": ["src/storage/models.py"],
            },
            {
                "description": "{ModelName}Repository sınıfı yaz",
                "files": ["src/storage/repository.py"],
                "depends_on": ["task-1"],
            },
            {
                "description": "Migration SQL ekle",
                "files": ["src/storage/migrations.py"],
                "depends_on": ["task-1"],
            },
            {
                "description": "Repository testleri yaz",
                "files": ["tests/test_storage/test_{model_lower}_repo.py"],
                "depends_on": ["task-2"],
            },
        ],
    },
    "add_llm_node": {
        "name": "LangGraph Node Ekle",
        "triggers": ["node ekle", "yeni node", "langgraph node"],
        "tasks": [
            {
                "description": "{NodeName} node fonksiyonu yaz",
                "files": ["src/graph/nodes/{node_lower}.py"],
            },
            {
                "description": "Graph'a edge ekle",
                "files": ["src/graph/builder.py"],
                "depends_on": ["task-1"],
            },
            {
                "description": "Node unit testi yaz",
                "files": ["tests/test_nodes/test_{node_lower}.py"],
                "depends_on": ["task-1"],
            },
        ],
    },
}

def find_template(user_message: str) -> dict | None:
    msg_lower = user_message.lower()
    for template_id, template in SPRINT_TEMPLATES.items():
        if any(trigger in msg_lower for trigger in template["triggers"]):
            return template
    return None
```

---

## References

- `sprint-task-decomposition-skill/SKILL.md` — görev ayrıştırma
- `feature-breakdown-skill/SKILL.md` — özellik ayrıştırma
- `planner-node-implementation-skill/SKILL.md` — planner
