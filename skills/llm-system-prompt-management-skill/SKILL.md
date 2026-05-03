---
name: llm-system-prompt-management
description: Coder AI için — farklı node'lar için farklı system prompt'ları yönetmek; prompt versiyonlama ve A/B testi.
---

## Purpose

Aynı system prompt her node için uygun değil.
Planner: yönetici tonu. Worker: teknik, odaklı. Reviewer: eleştirel.
Merkezi prompt yönetimi: değişiklik tek yerden yapılır.

---

## When to Apply

- Yeni LangGraph node'u oluşturulurken
- Prompt performansı değiştirilmek istendiğinde
- A/B test için iki prompt versiyonu denenirken

---

## Rules

- Her node'un kendi system prompt'u var.
- Prompt: versiyonlanır (v1, v2...).
- Değişken enjeksiyonu: `{project_name}`, `{language}` vb.
- Aktif versiyon: config veya env'den okunur.

---

## Guidelines

```python
from string import Template

SYSTEM_PROMPTS: dict[str, dict[str, str]] = {
    "planner": {
        "v1": "Sen bir yazılım proje yöneticisisin. Türkçe yanıt ver. Görevleri JSON formatında planla.",
        "v2": "Sen deneyimli bir teknik PM'sin. Kısa, net, eyleme geçirilebilir görevler üret. Türkçe konuş.",
    },
    "worker": {
        "v1": "Sen bir Python yazılımcısısın. Sadece kod yaz, açıklama ekleme.",
        "v2": "Sen kıdemli bir Python mühendisisin. Type hint, clean code, PEP8 uyumlu kod üret.",
    },
    "reviewer": {
        "v1": "Sen bir kod gözlemcisisin. Hataları bul, iyileştirme öner.",
        "v2": "Sen sıkı bir kod incelemecisisin. Güvenlik, performans, bakım açısından değerlendir.",
    },
}

def get_system_prompt(
    node: str,
    version: str | None = None,
    variables: dict | None = None,
) -> str:
    node_prompts = SYSTEM_PROMPTS.get(node, {})
    if not node_prompts:
        return ""
    
    ver = version or max(node_prompts.keys())
    prompt = node_prompts.get(ver, next(iter(node_prompts.values())))
    
    if variables:
        try:
            prompt = Template(prompt).safe_substitute(variables)
        except (KeyError, ValueError):
            pass
    
    return prompt

def list_prompt_versions(node: str) -> list[str]:
    return list(SYSTEM_PROMPTS.get(node, {}).keys())
```

---

## References

- `prompt-template-construction-skill/SKILL.md` — prompt şablonu
- `prompt-versioning-skill/SKILL.md` — prompt versiyonlama
- `context-injection-strategy-skill/SKILL.md` — bağlam enjeksiyonu
