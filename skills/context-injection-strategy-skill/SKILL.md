---
name: context-injection-strategy
description: Coder AI için — LLM prompt'una hangi bağlam bilgisinin, hangi sırada ve ne kadar ekleneceğine sistematik karar vermek.
---

## Purpose

Fazla bağlam token israf eder ve LLM'i yanıltır.
Az bağlam tutarsız kod üretimine yol açar.
Doğru bağlam stratejisi: kritik bilgi önce, destekleyici bilgi sonra.

---

## When to Apply

- Worker veya planner prompt'u oluşturulurken
- Bağlam dosyalarının sırası belirlenirken
- Prompt token limit optimizasyonu yapılırken

---

## Rules

- Sıralama: görev açıklaması → hedef dosya yolu → bağlam dosyaları.
- Bağlam dosyaları: en doğrudan bağlantılı ilk, genel son.
- Her bağlam dosyası: açıklayıcı başlık (`# File: path`) ile başlar.
- Toplam bağlam: `MAX_CONTEXT_CHARS` ile sınırlı.

---

## Guidelines

```python
CONTEXT_INJECTION_TEMPLATE = """
Görev: {task_description}

Hedef dosya: {target_file}

{context_section}

Yukarıdaki bağlamı kullanarak {target_file} dosyasını yaz.
Sadece Python kodu üret, açıklama ekleme.
"""

def build_context_section(
    context_files: dict[str, str],
    max_chars: int = 3000,
) -> str:
    if not context_files:
        return ""
    
    parts = ["İlgili dosyalar:"]
    used = 0
    
    for path, content in context_files.items():
        header = f"\n# File: {path}\n"
        available = max_chars - used - len(header)
        
        if available <= 0:
            break
        
        truncated = content[:available]
        if len(content) > available:
            truncated += "\n# ... [kırpıldı]"
        
        parts.append(header + truncated)
        used += len(header) + len(truncated)
    
    return "\n".join(parts)

def build_worker_prompt_structured(
    task: dict,
    target_file: str,
    context_files: dict[str, str],
) -> list:
    context_section = build_context_section(context_files)
    
    human_content = CONTEXT_INJECTION_TEMPLATE.format(
        task_description=task["description"],
        target_file=target_file,
        context_section=context_section,
    )
    
    return [
        SystemMessage(content="Sen kıdemli bir Python geliştiricisisin."),
        HumanMessage(content=human_content),
    ]
```

---

## References

- `prompt-template-construction-skill/SKILL.md` — prompt yapısı
- `file-context-loader-skill/SKILL.md` — dosya yükleme
- `context-window-management-skill/SKILL.md` — token yönetimi
