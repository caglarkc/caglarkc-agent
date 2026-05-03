---
name: sprint-clone
description: Planner AI için — başarılı bir sprint'i şablon olarak kullanarak benzer yeni sprint oluşturmak; sıfırdan planlamayı atlamak.
---

## Purpose

"Önceki authentication sprint gibi bir sprint yapalım" isteği gelirse sıfırdan plan yazmak gerekmez.
Clone: önceki sprint'in görev yapısı kopyalanır, dosya isimleri güncellenir.
Kullanıcı farkları belirtir, geri kalan otomatik doldurilur.

---

## When to Apply

- Benzer iki sprint yapısı tekrar ettiğinde
- "Şu sprint gibi bir tane daha" denildiğinde
- Sprint şablonu sisteminin temeli kurulurken

---

## Rules

- Clone: görev yapısı kopyalanır, sprint_id yenilenir.
- Dosya isimleri: model adı değişirse güncellenir.
- Kullanıcıya farklar gösterilir, onay alınır.
- Orijinal sprint referansı yeni sprint'e not olarak eklenir.

---

## Guidelines

```python
async def clone_sprint(
    source_sprint_id: str,
    new_description: str,
    name_replacements: dict[str, str],
    repo: ProjectRepository,
) -> Sprint:
    source = await repo.get_sprint(source_sprint_id)
    if not source:
        raise ValueError(f"Kaynak sprint bulunamadı: {source_sprint_id}")
    
    new_sprint_id = f"sprint-{uuid4()}"
    
    # Görevleri kopyala, isimleri güncelle
    new_tasks = []
    new_file_registry = {}
    
    for task in (source.tasks or []):
        new_task = dict(task)
        new_task["task_id"] = f"task-{uuid4()}"
        
        # Dosya isimlerini güncelle
        new_files = []
        for f in task.get("files", []):
            new_f = f
            for old, new in name_replacements.items():
                new_f = new_f.replace(old, new)
            new_files.append(new_f)
            new_file_registry[new_f] = "planned"
        
        new_task["files"] = new_files
        new_task["description"] = _replace_names(
            task["description"], name_replacements
        )
        new_tasks.append(new_task)
    
    new_sprint = Sprint(
        sprint_id=new_sprint_id,
        project_id=source.project_id,
        status=SprintStatus.DRAFT,
        tasks=new_tasks,
        summary=f"{new_description} (Klonlanan: {source_sprint_id})",
        file_registry=new_file_registry,
    )
    
    await repo.create_sprint(new_sprint)
    logger.info(f"Sprint klonlandı: {source_sprint_id} → {new_sprint_id}")
    return new_sprint

def _replace_names(text: str, replacements: dict[str, str]) -> str:
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text
```

---

## References

- `sprint-template-library-skill/SKILL.md` — şablon kütüphanesi
- `sprint-history-query-skill/SKILL.md` — geçmiş sorgu
- `sprint-plan-revision-skill/SKILL.md` — plan revizyonu
