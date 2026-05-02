---
name: dependency-injection-patterns
description: Coder AI için — repository, LLM client ve event bus gibi bağımlılıkları node ve servislere doğru şekilde enjekte etmek; test edilebilirliği artırmak.
---

## Purpose

Hard-coded bağımlılıklar (global import) test etmeyi ve değiştirmeyi zorlaştırır.
DI ile bağımlılıklar dışarıdan verilir — mock ile değiştirilebilir.
LangGraph node'larında DI, closure veya LangGraph config ile yapılır.

---

## When to Apply

- Node fonksiyonu yazılırken (repository, LLM alması gerektiğinde)
- Servis sınıfı tasarlanırken
- Test için bağımlılıklar mock'lanacakken

---

## Rules

- Global singleton'lar (EventBus) kabul edilir — değiştirilmez.
- Repository ve LLM: closure ile node'a inject edilir.
- `RunnableConfig` üzerinden LangGraph config'i okuma: test override için.
- Constructor injection: servis sınıfları için standart yöntem.

---

## Guidelines

```python
# Closure ile DI (LangGraph node'ları için)
def make_planner_node(
    repo: ProjectRepository,
    llm: BaseChatModel,
) -> Callable:
    async def planner_node(state: OrchestratorState) -> OrchestratorState:
        # repo ve llm burada kapalı değişken
        project = await repo.get_project(state["project_id"])
        response = await llm.ainvoke(build_prompt(project, state))
        ...
    return planner_node

# Graph build sırasında inject et
repo = ProjectRepository(settings.db_path)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

builder.add_node("planner", make_planner_node(repo, llm))
```

Servis sınıfı constructor injection:
```python
class SprintService:
    def __init__(
        self,
        repo: ProjectRepository,
        event_bus: EventBus,
        llm: BaseChatModel,
    ):
        self._repo = repo
        self._event_bus = event_bus
        self._llm = llm
    
    async def create_sprint(self, request: CreateSprintRequest) -> Sprint:
        ...
```

Test'te mock inject:
```python
async def test_planner_node():
    mock_repo = AsyncMock(spec=ProjectRepository)
    mock_llm = AsyncMock(spec=BaseChatModel)
    
    node = make_planner_node(mock_repo, mock_llm)
    result = await node(initial_state)
    mock_llm.ainvoke.assert_called_once()
```

---

## References

- `graph-node-isolation-test-skill/SKILL.md` — node testi
- `node-function-signature-skill/SKILL.md` — node imzası
- `event-bus-patterns-skill/SKILL.md` — event bus
