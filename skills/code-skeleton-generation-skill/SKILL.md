---
name: code-skeleton-generation
description: Coder AI için — görev açıklamasından önce kod iskeleti (stub) oluşturmak; sonra detayları doldurmak.
---

## Purpose

Doğrudan tam kod üretmek yerine iskelet + doldurma iki aşamalı yaklaşım daha iyi çıktı verir.
İskelet: sınıf yapısı, metod imzaları, type hints — gövde yok.
İkinci geçiş: her metodu bağımsız doldurur, bağlam küçük kalır.

---

## When to Apply

- Büyük sınıf veya modül üretilirken
- Birden fazla metod içeren dosya yazılırken
- Test üretimi önce iskelet + sonra implementasyon yapılırken

---

## Rules

- İskelet: `pass` veya `...` gövdeli metodlar.
- Type hint ve docstring ilk geçişte yazılır.
- Doldurma: her metod ayrı LLM çağrısıyla doldurulur (bağlam kirliliği önlenir).
- Final: tam dosya birleştirilir, linter'dan geçirilir.

---

## Guidelines

```python
SKELETON_PROMPT = """
Şu görev için Python sınıfı iskeleti oluştur.
Sadece sınıf tanımı, metodların imzaları ve type hint'leri yaz.
Gövdelere sadece `pass` yaz, hiçbir implementasyon kodu ekleme.

Görev: {task_description}
Dosya: {file_path}
"""

FILL_METHOD_PROMPT = """
Şu Python metodunu implement et:

Sınıf: {class_name}
Metod imzası: {method_signature}
Docstring: {docstring}
Bağlam (diğer metodlar): {context}

Sadece metod gövdesini yaz, imzayı tekrarlama.
"""

async def generate_with_skeleton(
    llm,
    task: dict,
) -> str:
    # 1. İskelet üret
    skeleton = await llm.ainvoke([
        HumanMessage(content=SKELETON_PROMPT.format(
            task_description=task["description"],
            file_path=task["file_path"],
        ))
    ])
    
    # 2. Her metod için gövde üret
    methods = extract_method_signatures(skeleton.content)
    filled  = skeleton.content
    
    for method in methods:
        body = await llm.ainvoke([
            HumanMessage(content=FILL_METHOD_PROMPT.format(
                class_name=task.get("class_name", ""),
                method_signature=method["signature"],
                docstring=method.get("docstring", ""),
                context=method.get("context", ""),
            ))
        ])
        filled = filled.replace(
            f"{method['signature']}\n        pass",
            f"{method['signature']}\n{indent(body.content, 8)}",
        )
    
    return filled

def indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line for line in text.splitlines())
```

---

## References

- `code-generation-templates-skill/SKILL.md` — şablon tabanlı üretim
- `llm-prompt-chaining-skill/SKILL.md` — zincirleme prompt
- `file-template-registry-skill/SKILL.md` — dosya şablonları
