---
name: prompt-versioning
description: Planner AI için — LLM prompt'larını versiyonlamak; hangi prompt değişikliğinin hangi sonucu ürettiğini takip etmek.
---

## Purpose

Prompt değişikliği çıktı kalitesini dramatik değiştirebilir.
Versiyonlama, hangi prompt'un hangi sprint'te kullanıldığını gösterir.
Regresyon: eski prompt'a geri dönmek mümkün olur.

---

## When to Apply

- Planner veya worker prompt'u değiştirilirken
- A/B test için farklı prompt versiyonları karşılaştırılırken
- Çıktı kalitesi düştüğünde prompt değişikliği şüphelenildiğinde

---

## Rules

- Her prompt: sabit versiyon string'i (`v1`, `v2`) içerir.
- Versiyon: sprint metadata'sına kaydedilir.
- Prompt değişikliği: ADR ile belgelenir.
- Eski versiyon silinmez — `DEPRECATED` ile işaretlenir.

---

## Guidelines

```python
# src/core/prompts.py

PLANNER_SYSTEM_V1 = """..."""  # DEPRECATED

PLANNER_SYSTEM_V2 = """Sen bir yazılım geliştirme yöneticisisin.
[v2: Görev bağımlılıkları ve dosya listesi zorunlu]
Kullanıcının isteğini analiz ederek sprint planı oluşturuyorsun.

Çıktı formatı:
{
  "tasks": [
    {
      "task_id": "task-1",
      "description": "...",
      "files": ["src/..."],
      "depends_on": []
    }
  ],
  "summary": "Sprint hedefi"
}
"""

CURRENT_PLANNER_VERSION = "v2"
PROMPT_REGISTRY = {
    "planner_system_v1": PLANNER_SYSTEM_V1,
    "planner_system_v2": PLANNER_SYSTEM_V2,
}

def get_prompt(name: str, version: str | None = None) -> str:
    key = f"{name}_{version}" if version else f"{name}_{CURRENT_PLANNER_VERSION}"
    prompt = PROMPT_REGISTRY.get(key)
    if not prompt:
        raise KeyError(f"Prompt bulunamadı: {key}")
    return prompt

# Sprint metadata'ya kayıt
async def log_prompt_version(
    sprint_id: str,
    prompt_name: str,
    version: str,
    repo: ProjectRepository,
) -> None:
    await repo.create_decision(Decision(
        sprint_id=sprint_id,
        summary=f"Prompt kullanıldı: {prompt_name}@{version}",
        rationale=f"Planner {version} versiyonu ile çalıştı",
        decision_type="technical",
    ))
```

---

## References

- `architecture-decision-record-skill/SKILL.md` — ADR
- `prompt-template-construction-skill/SKILL.md` — prompt oluşturma
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
