---
name: sprint-history-query
description: Planner AI için — tamamlanan sprint'lerin geçmişini sorgulamak; önceki kararları ve sonuçları yeni sprint planında bağlam olarak kullanmak.
---

## Purpose

Önceki sprint'lerin ne yaptığı bilinmeden yeni plan yapılamaz.
"Bu dosya daha önce yazıldı mı?" sorusu sprint geçmişinden yanıtlanır.
Tekrar eden hatalar geçmiş sprint verisiyle önlenir.

---

## When to Apply

- Yeni sprint planlanmadan önce bağlam toplanırken
- Kullanıcı "daha önce ne yaptık?" diye sorduğunda
- Mevcut dosyaların son sprint'te yazılıp yazılmadığı kontrol edilirken

---

## Rules

- Sadece `done` durumdaki sprint'ler geçmiş sayılır.
- Son 3 sprint yeterli — daha eskisi gereksiz bağlam.
- Özet bilgi yeterli — tam plan tekrar yüklenmez.
- Geçmiş sprint dosya listesi new sprint'in file_registry'sine kılavuzluk eder.

---

## Guidelines

```python
async def get_sprint_history_context(
    project_id: str,
    repo: ProjectRepository,
    limit: int = 3
) -> str:
    sprints = await repo.list_sprints(
        project_id=project_id,
        status="done",
        limit=limit,
        order_by="created_at DESC",
    )
    
    if not sprints:
        return "Henüz tamamlanmış sprint yok."
    
    lines = []
    for sprint in sprints:
        done_count = sum(
            1 for s in sprint.file_registry.values()
            if s == "done"
        )
        lines.append(
            f"Sprint {sprint.sprint_id}: {sprint.summary} "
            f"({done_count} dosya, {sprint.created_at.date()})"
        )
    
    return "Önceki sprint'ler:\n" + "\n".join(lines)

async def get_existing_files(
    project_id: str,
    repo: ProjectRepository
) -> list[str]:
    """Tüm tamamlanmış dosyaları döndür."""
    sprints = await repo.list_sprints(project_id=project_id, status="done")
    files = set()
    for sprint in sprints:
        for path, status in sprint.file_registry.items():
            if status == "done":
                files.add(path)
    return sorted(files)
```

---

## References

- `decision-log-maintenance-skill/SKILL.md` — karar geçmişi
- `sprint-summary-generation-skill/SKILL.md` — sprint özeti
- `context-window-management-skill/SKILL.md` — bağlam yönetimi
