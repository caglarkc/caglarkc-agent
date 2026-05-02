---
name: multi-project-support
description: Planner AI için — aynı agent instance'ının birden fazla projeyi eş zamanlı yönetmesini sağlamak; project_id ile izolasyon.
---

## Purpose

Kullanıcının birden fazla projesi varsa her biri izole çalışmalı.
`project_id` tüm operasyonlarda primary key görevi görür.
LangGraph thread_id = project_id ile checkpoint izolasyonu sağlanır.

---

## When to Apply

- Kullanıcı "proje listele" veya "projeye geç" komutu verdiğinde
- PM mode hangi proje üzerinde çalıştığını bilmek istediğinde
- Multi-project CLI veya Telegram komutu yazılırken

---

## Rules

- Her proje ayrı `thread_id` ile checkpoint'te saklanır.
- Aktif proje: session'da tutulur — her komutta tekrar sorulmaz.
- Proje geçişi: mevcut sprint'i interrupt et, yeni proje state'ini yükle.
- Proje silme yoktur — `status="archived"` yapılır.

---

## Guidelines

```python
# src/core/project_manager.py
class ProjectManager:
    def __init__(self, repo: ProjectRepository, compiled_graph):
        self._repo = repo
        self._graph = compiled_graph
        self._active_project_id: str | None = None
    
    async def list_projects(self) -> list[Project]:
        return await self._repo.list_projects(status="active")
    
    async def switch_project(self, project_id: str) -> Project:
        project = await self._repo.get_project(project_id)
        if not project:
            raise ValueError(f"Proje bulunamadı: {project_id}")
        self._active_project_id = project_id
        logger.info(f"Aktif proje: {project_id}")
        return project
    
    @property
    def active_project_id(self) -> str:
        if not self._active_project_id:
            raise RuntimeError("Aktif proje seçilmemiş")
        return self._active_project_id
    
    async def get_active_project_state(self) -> OrchestratorState | None:
        config = get_thread_config(self.active_project_id)
        snapshot = await self._graph.aget_state(config=config)
        return snapshot.values if snapshot else None
```

PM mesaj formatı:
```
[SOHBET] Mevcut projeler:

1. caglarkc-agent (Aktif) — Son sprint: 3
2. my-api-project — Son sprint: 1
3. data-pipeline — Sprint yok

Proje değiştirmek için: "2. projeye geç"
```

---

## References

- `thread-config-usage-skill/SKILL.md` — thread config
- `project-initialization-workflow-skill/SKILL.md` — proje başlatma
- `sprint-lifecycle-state-machine-skill/SKILL.md` — sprint durumu
