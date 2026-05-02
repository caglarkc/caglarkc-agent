---
name: prompt-template-construction
description: Coder AI için — LLM'e gönderilecek prompt'u system/human mesajı ayrımıyla doğru yapıda oluşturmak; context injection yapmak.
---

## Purpose

İyi yapılandırılmış prompt daha iyi LLM çıktısı üretir.
System mesajı rol ve kısıtları tanımlar; human mesajı görevi verir.
Context injection (dosya içerikleri, mevcut state) insan mesajına eklenir.

---

## When to Apply

- Planner node için LLM mesajları oluşturulurken
- Worker node için kod üretme prompt'u hazırlanırken
- Reviewer node için kod inceleme prompt'u yazılırken

---

## Rules

- System mesajı: rol, format, kısıtları belirler — değişmez.
- Human mesajı: her çağrıda değişen dinamik içerik.
- Context dosyaları: human mesajına `<context>` tag ile eklenir.
- Prompt 8000 token'ı aşmamalı — gerekirse context kısaltılır.
- JSON çıktı isteniyorsa: format örneği system mesajına eklenir.

---

## Guidelines

```python
from langchain_core.messages import SystemMessage, HumanMessage

PLANNER_SYSTEM = """Sen bir yazılım geliştirme yöneticisisin.
Kullanıcının isteğini analiz ederek sprint planı oluşturuyorsun.

Çıktın her zaman şu JSON formatında olmalı:
{
  "tasks": [{"task_id": "...", "description": "...", "files": [...]}],
  "summary": "..."
}

Kurallar:
- Görevler bağımsız ve somut olmalı
- Her görev için etkilenecek dosyalar listelenmeli
- Türkçe açıklama yaz
"""

def build_planner_prompt(
    user_request: str,
    project_context: str,
    existing_files: list[str]
) -> list:
    human_content = f"""Kullanıcı isteği: {user_request}

<context>
Mevcut proje yapısı:
{project_context}

Mevcut dosyalar:
{chr(10).join(existing_files[:20])}
</context>

Lütfen sprint planı oluştur."""

    return [
        SystemMessage(content=PLANNER_SYSTEM),
        HumanMessage(content=human_content),
    ]

def build_coder_prompt(
    task_description: str,
    file_path: str,
    context_files: dict[str, str]
) -> list:
    context_block = "\n".join(
        f"<file path='{path}'>\n{content}\n</file>"
        for path, content in context_files.items()
    )
    
    return [
        SystemMessage(content="Sen bir Python yazılım geliştiricisin. Verilen görevi implemente et."),
        HumanMessage(content=f"Görev: {task_description}\nDosya: {file_path}\n\n{context_block}"),
    ]
```

---

## References

- `planner-node-implementation-skill/SKILL.md` — planner
- `worker-node-implementation-skill/SKILL.md` — worker
- `llm-output-parsing-skill/SKILL.md` — çıktı parse
