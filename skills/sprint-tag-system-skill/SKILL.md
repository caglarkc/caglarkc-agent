---
name: sprint-tag-system
description: Planner AI için — sprint'leri etiketleyerek (feature, bugfix, refactor, test) filtreleme ve raporlama yapmak.
---

## Purpose

"Bugfix sprint'lerimin başarı oranı ne?" sorusu etiket olmadan cevaplanamaz.
Tag sistemi sprint'leri kategorize eder; analiz ve raporlama kolaylaşır.
Kullanıcı "önceki tüm test sprint'lerini listele" diyebilir.

---

## When to Apply

- Sprint planlanırken otomatik tag atanırken
- Sprint listesi filtrelenirken
- Sprint tiplerine göre metrik karşılaştırılırken

---

## Rules

- Sprint her zaman en az 1 tag alır.
- Otomatik tag: plan içeriğinden tespit edilir.
- Manuel tag: kullanıcı ekleyebilir.
- Tag'ler küçük harf, tire ile ayrılır: `feature`, `bug-fix`, `refactor`.

---

## Guidelines

```python
SPRINT_TAG_PATTERNS = {
    "feature":   ["ekle", "yeni", "oluştur", "implement", "entegre"],
    "bug-fix":   ["düzelt", "hata", "fix", "broken", "çalışmıyor"],
    "refactor":  ["refactor", "temizle", "yeniden yaz", "basitleştir"],
    "test":      ["test", "spec", "coverage"],
    "docs":      ["dokümantasyon", "readme", "yorum", "açıkla"],
    "infra":     ["konfigürasyon", "docker", "ci", "deploy", "migration"],
}

def auto_tag_sprint(description: str) -> list[str]:
    desc_lower = description.lower()
    tags = []
    
    for tag, keywords in SPRINT_TAG_PATTERNS.items():
        if any(kw in desc_lower for kw in keywords):
            tags.append(tag)
    
    return tags or ["general"]

# DB modeli
class Sprint(BaseModel):
    sprint_id: str
    tags: list[str] = Field(default_factory=list)
    ...

# Repository filtre
async def list_sprints_by_tag(
    project_id: str,
    tag: str,
    repo: ProjectRepository,
) -> list[Sprint]:
    all_sprints = await repo.list_sprints(project_id=project_id)
    return [s for s in all_sprints if tag in (s.tags or [])]
```

PM mesaj:
```
[PLANLAMA] Sprint etiketlendi: feature, test

Bu bir özellik ekleme sprint'i.
Geçmiş feature sprint'lerinizin başarı oranı: %87
```

---

## References

- `sprint-metrics-collection-skill/SKILL.md` — metrikler
- `sprint-history-query-skill/SKILL.md` — geçmiş sorgu
- `sprint-type-selection-skill/SKILL.md` — sprint tipi
