---
name: project-initialization-workflow
description: Planner AI için — yeni proje oluşturma isteğinde proje kaydını DB'ye eklemek, ilk sprint hazırlığını yapmak ve kullanıcıyı karşılamak.
---

## Purpose

İlk sprint öncesinde proje DB'de kaydedilmiş olmalı.
`project_id` oluşturulur, proje kaydı açılır, kullanıcıya onay mesajı gider.
Bu adım atlanırsa sonraki sprint'lerde `project_id` bulunamaz.

---

## When to Apply

- Kullanıcı yeni proje başlatmak istediğinde
- `CREATE` veya `NEW PROJECT` komutu geldiğinde
- Mevcut proje listesinde aranan proje yoksa

---

## Rules

- `project_id`: UUID veya kullanıcı tanımlı kısa ad.
- Proje DB'ye kaydedilir: `projects` tablosu.
- İlk sprint'e geçmeden önce kullanıcıdan onay alınır.
- Proje adı: 3-100 karakter, alfanumerik + tire/alt çizgi.

---

## Guidelines

```python
async def initialize_project(
    name: str,
    description: str,
    repo: ProjectRepository
) -> Project:
    project = Project(
        project_id=slugify(name),  # veya uuid
        name=name,
        description=description,
        status="active",
    )
    await repo.create_project(project)
    logger.info(f"Proje oluşturuldu: {project.project_id}")
    return project

def slugify(name: str) -> str:
    import re
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9_-]', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:50]
```

PM'in karşılama mesajı:
```
[SOHBET] Proje başlatıldı!

Proje: caglarkc-agent
ID: caglarkc-agent
Durum: Aktif

Şimdi ilk sprint için ne yapmak istediğinizi anlatın.
Örnek: "LangGraph graph yapısını kur, temel node'ları oluştur"
```

---

## References

- `pm-mode-skill/SKILL.md` — PM konuşma modları
- `aiosqlite-patterns-skill/SKILL.md` — DB kayıt
- `sprint-goal-articulation-skill/SKILL.md` — sprint hedefi
