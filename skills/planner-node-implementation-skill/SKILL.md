---
name: planner-node-implementation
description: Coder AI için — LangGraph planner node'unu implemente etmek; kullanıcı isteğini sprint görevlerine ve dosya listesine dönüştürmek.
---

## Purpose

Planner node, sistemin giriş kapısıdır — kullanıcı isteğini anlamlı görevlere çevirir.
LLM ile konuşur, sprint planı oluşturur, DB'ye kaydeder.
Çıktı: `tasks` listesi, `file_registry` (hepsi `planned`), `sprint_id`.

---

## When to Apply

- `src/graph/nodes/planner.py` yazılırken
- Sprint oluşturma mantığı implemente edilirken
- LLM ile plan üretimi entegre edilirken

---

## Rules

- Planner, kullanıcı mesajını `state["messages"]`'dan alır.
- LLM çıktısı Pydantic ile doğrulanır.
- Sprint DB'ye kaydedilir.
- `file_registry`: tüm dosyalar `"planned"` ile başlar.
- Mevcut sprint varsa: güncelleme değil, yeni sprint oluşturulur.

---

## Guidelines

```python
# src/graph/nodes/planner.py
async def planner_node(state: OrchestratorState) -> OrchestratorState:
    project_id = state["project_id"]
    messages = state.get("messages", [])
    
    # LLM ile plan oluştur
    prompt = build_planner_prompt(
        user_request=_extract_last_user_message(messages),
        project_context=await _get_project_context(project_id),
        existing_files=await _list_project_files(project_id),
    )
    
    response = await llm.ainvoke(prompt)
    plan = await parse_llm_json(response.content, LLMPlanOutput)
    
    # Sprint oluştur
    sprint_id = f"sprint-{uuid4()}"
    sprint = Sprint(
        sprint_id=sprint_id,
        project_id=project_id,
        status=SprintStatus.DRAFT,
        tasks=[t.model_dump() for t in plan.tasks],
    )
    await repo.create_sprint(sprint)
    
    # File registry hazırla
    all_files = [f for t in plan.tasks for f in t.files]
    file_registry = {f: "planned" for f in all_files}
    
    logger.info(f"Sprint planlandı: {sprint_id}, {len(all_files)} dosya")
    
    return {
        "sprint_id": sprint_id,
        "tasks": [t.model_dump() for t in plan.tasks],
        "file_registry": file_registry,
        "sprint_summary": plan.summary,
    }
```

---

## References

- `node-function-signature-skill/SKILL.md` — node imzası
- `prompt-template-construction-skill/SKILL.md` — prompt
- `llm-output-parsing-skill/SKILL.md` — çıktı parse
