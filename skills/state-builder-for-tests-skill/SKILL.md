---
name: state-builder-for-tests
description: Coder AI için — LangGraph node testleri için hazır, eksiksiz OrchestratorState nesneleri oluşturma; farklı senaryolar için state builder fonksiyonları.
---

## Purpose

Her test için manuel state dict oluşturmak yerine builder fonksiyonlar sağlar.
Tutarlı ve bakımı kolay test state'leri üretir.
Farklı test senaryoları için özelleştirilebilir hazır state'ler sunar.

---

## When to Apply

- LangGraph node test edilirken
- Dispatcher, worker veya reviewer senaryoları test edilirken
- Farklı state kombinasyonları gerektiren parametrized testlerde

---

## Rules

- Test state'leri gerçek proje verisi içermez (UUID'ler "test-" prefix ile).
- `build_initial_state()` temel state için kullanılır, üzerine ekleme yapılır.
- Her senaryo için ayrı builder fonksiyon veya fixture.
- State'ler immutable değil ama test içinde mutate edilmez.

---

## Guidelines

Test state builder'ları:
```python
# tests/helpers/state_builders.py

from src.graph.state import OrchestratorState, build_initial_state


def make_base_state(
    project_id: str = "test-project-001",
    task: str = "Test görevi"
) -> OrchestratorState:
    return build_initial_state(project_id=project_id, task=task)


def make_state_with_plan(
    files: list[str] | None = None
) -> OrchestratorState:
    state = make_base_state()
    files = files or ["src/test.py"]
    state.update({
        "draft_plan": {
            "summary": "Test planı",
            "sprint_type": "feature",
            "files": files,
            "dependencies": {}
        },
        "worker_queue": [
            {
                "assignment": {
                    "worker_id": "worker_a",
                    "target_file": f,
                    "task_type": "write_file",
                    "description": f"{f} yaz"
                },
                "status": "planned",
                "dependencies": [],
                "retry_count": 0
            }
            for f in files
        ],
        "file_registry": {f: "planned" for f in files}
    })
    return state


def make_state_with_failed_worker(
    target_file: str = "src/test.py",
    error: str = "LLM timeout"
) -> OrchestratorState:
    state = make_state_with_plan([target_file])
    state.update({
        "file_registry": {target_file: "failed"},
        "errors": [{"node": "worker", "error": error}]
    })
    return state


def make_state_awaiting_approval() -> OrchestratorState:
    state = make_state_with_plan()
    state["approval_request"] = {
        "approval_id": "test-approval-001",
        "project_id": state["project_id"],
        "reason": "Plan onayı",
        "status": "pending"
    }
    return state
```

---

## References

- `pytest-async-test-skill/SKILL.md` — test yapısı
- `state-typeddict-definition-skill/SKILL.md` — state şeması
- `graph-node-isolation-test-skill/SKILL.md` — node izolasyonu
