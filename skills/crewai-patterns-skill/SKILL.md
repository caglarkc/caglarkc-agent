---
name: crewai-patterns
description: AI Development Team Orchestrator projesinde CrewAI kullanım kuralları ve pattern'ları. Hierarchical process kurulumu, Gemini manager tanımı, Ollama + OpenRouter mixed provider, dinamik rol atama, human-in-the-loop, Flow yapısı. CrewAI kodu yazarken veya review ederken referans alınır.
---

## Temel Kurulum

### Hierarchical Crew

```python
from crewai import Crew, Agent, Task, Process
from crewai import LLM

# Manager — Gemini
gemini_llm = LLM(
    model="gemini/gemini-2.5-pro",
    api_key=settings.GEMINI_API_KEY
)

# Worker 1 — Ollama Qwen2.5
ollama_llm = LLM(
    model="ollama/qwen2.5-coder",
    base_url=settings.OLLAMA_HOST
)

# Worker 2 — OpenRouter
or1_llm = LLM(
    model=f"openrouter/{settings.OPENROUTER_MODEL_1}",
    api_key=settings.OPENROUTER_API_KEY_1,
    base_url="https://openrouter.ai/api/v1"
)

# Worker 3 — OpenRouter
or2_llm = LLM(
    model=f"openrouter/{settings.OPENROUTER_MODEL_2}",
    api_key=settings.OPENROUTER_API_KEY_2,
    base_url="https://openrouter.ai/api/v1"
)

crew = Crew(
    agents=[worker1, worker2, worker3],
    tasks=tasks,
    process=Process.hierarchical,
    manager_llm=gemini_llm,  # Gemini otomatik manager olur
    verbose=True
)
```

---

## Dinamik Rol Atama

Worker rolleri her sprint başında değişir. Template interpolation ile yapılır:

```python
# agents.yaml
worker_1:
  role: "{sprint_role_1}"
  goal: "{sprint_goal_1}"
  backstory: "Sen {sprint_role_1} konusunda uzman bir yazılım geliştiricisisin."

# Crew kickoff
crew.kickoff(inputs={
    "sprint_role_1": "Backend API Developer",
    "sprint_goal_1": "Auth ve user endpoint'lerini yaz",
    "sprint_role_2": "Frontend Developer",
    "sprint_goal_2": "Login ve register sayfalarını yaz",
    "sprint_role_3": "Database Engineer",
    "sprint_goal_3": "Schema ve migration dosyalarını oluştur",
    "project_path": "/projects/my-app",
    "sprint_number": 1
})
```

---

## Human-in-the-Loop

Tek mekanizma: Task seviyesi `human_input=True`.

```python
# Plan onayı — kullanıcı görmeden sprint başlamaz
plan_approval_task = Task(
    description="Üretilen sprint planını sun ve onay bekle",
    expected_output="Kullanıcı onayı alındı",
    agent=manager_agent,
    human_input=True  # Burada durur, kullanıcı girdisi bekler
)
```

> **Not**: Faz 2'de onay konsoldan alınır. Faz 5/6 tamamlanınca FlowManager, EventBus üzerinden CLI/Telegram onayını yakalar ve flow.resume() ile devam ettirir. `human_input=True` o fazda devre dışı bırakılır.

Flow'da onay noktası bu pattern ile yönetilir:

```python
from crewai.flow.flow import Flow, listen, start

class OrchestratorFlow(Flow):

    @start()
    async def receive_task(self):
        return self.state.task

    @listen(receive_task)
    async def generate_plan(self, task):
        context = await context_builder.build(self.state.project_id)
        result = await self.planning_crew.kickoff_async(inputs={
            "task": task,
            "context": context  # Gemini önceki geçmişi burada görür
        })
        self.state.plan = result.raw
        self.state.flow_id = self.flow_id
        return result

    @listen(generate_plan)
    async def await_plan_approval(self, plan):
        # EventBus'a emit et — CLI/Telegram yakalar
        await bus.emit("plan.approval_needed", {
            "flow_id": self.flow_id,
            "plan": self.state.plan
        })
        # Flow burada pause olur (SQLite'a kaydedilir)
        # FlowManager.on_plan_approved() → flow.resume() ile devam eder

    @listen("approved")
    async def start_sprint(self):
        await self.run_sprint()
```

---

## Flow Pause / Resume

```python
# Flow durdurulur, SQLite'a kaydedilir
# Telegram'dan onay gelince:

async def resume_flow_from_telegram(flow_id: str, feedback: str):
    flow = OrchestratorFlow.from_pending(
        flow_id=flow_id,
        persistence=sqlite_persistence
    )
    await flow.resume(feedback=feedback)
```

---

## File Tools

```python
from crewai_tools import FileWriterTool, FileReadTool, DirectoryReadTool

file_writer = FileWriterTool()
file_reader = FileReadTool()
dir_reader = DirectoryReadTool()

worker1 = Agent(
    role="{sprint_role_1}",
    goal="{sprint_goal_1}",
    backstory="...",
    llm=ollama_llm,
    tools=[file_writer, file_reader, dir_reader]
)
```

---

## Kritik Kurallar

- `Process.hierarchical` dışında process kullanılmaz
- Manager agent direkt tool çağırmaz, worker'lara delege eder
- Her agent kendi `llm` ile tanımlanır — global LLM ayarlanmaz
- `kickoff_async()` kullanılır, `kickoff()` değil (async zorunlu)
- `human_input=True` olan task'lar onay noktasıdır — atlanamaz (Faz 2 konsol, Faz 5/6 sonrası replace edilir)
- Worker'lar sadece kendi sprint assignment'larındaki path'lere yazar
- Review döngüsü: worker biter → manager review → hata varsa tekrar → max 3 döngü
- Her `kickoff_async()` çağrısında `"context"` key'i inputs'a eklenir — `ContextBuilder.build()` ile üretilir
- `@human_feedback` decorator kullanılmaz — versiyona göre davranışı değişken, `human_input=True` tercih edilir

---

## Review Döngüsü Pattern

```python
MAX_REVIEW_CYCLES = 3

async def run_with_review(sprint_tasks, sprint_id):
    cycles = 0
    while cycles < MAX_REVIEW_CYCLES:
        # Worker'lar çalışır
        result = await worker_crew.kickoff_async(inputs=sprint_inputs)

        # Manager review eder
        review = await manager_review(result)

        if review.status == "approved":
            return result
        elif review.status == "revision_needed":
            sprint_inputs["revision_notes"] = review.notes
            cycles += 1
        else:
            raise SprintFailedError(f"Sprint {sprint_id} başarısız")

    raise MaxReviewCyclesError(f"Sprint {sprint_id} max döngüye ulaştı")
```

---

## Context Inject Pattern

Gemini her çağrıda stateless başlar. `ContextBuilder` geçmişi prompt'a inject eder:

```python
# src/core/context_builder.py
class ContextBuilder:
    MAX_TOKENS = 2000  # Yaklaşık karakter sınırı

    def __init__(self, repository: Repository):
        self.repo = repository

    async def build(self, project_id: str) -> str:
        project = await self.repo.get_project(project_id)
        sprints = await self.repo.get_recent_sprints(project_id, limit=3)
        decisions = await self.repo.get_decisions(project_id, limit=5)

        lines = [
            f"Aktif Proje: {project.name} | Sprint: {project.current_sprint} | Durum: {project.status}",
            f"Tamamlanan Sprintler: {len(sprints)} sprint",
        ]
        for s in sprints:
            lines.append(f"  Sprint {s.number}: {s.status} | {len(s.files_written)} dosya")
        if decisions:
            lines.append("Mimari Kararlar:")
            for d in decisions[-5:]:
                lines.append(f"  - {d.summary}")

        context = "\n".join(lines)
        # Token bütçesi kontrolü
        if len(context) > self.MAX_TOKENS * 4:
            context = context[:self.MAX_TOKENS * 4] + "\n[...özet kısaltıldı]"
        return context

# Kullanım — her crew kickoff öncesi
context = await context_builder.build(project_id)
result = await crew.kickoff_async(inputs={
    "task": task_description,
    "context": context,
    "sprint_role_1": "Backend API Developer",
    # ...diğer sprint inputs
})
```

---

## References

- CrewAI docs: https://docs.crewai.com
- `project-architecture/SKILL.md` — dosya path'leri, sınırlar ve context inject şeması