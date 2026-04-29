---
name: langgraph-patterns
description: AI Development Team Orchestrator projesinde LangGraph kullanım kuralları ve pattern'ları. OrchestratorState tanımı, node yapısı, koşullu edge'ler, DAG bağımlılık yönetimi, human-in-the-loop (interrupt), SqliteSaver persistence, context inject. LangGraph kodu yazarken veya review ederken referans alınır.
---

## Temel Kurulum

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import interrupt

# Graph tanımı
builder = StateGraph(OrchestratorState)

# Node'ları ekle
builder.add_node("planner", planner_node)
builder.add_node("await_approval", await_approval_node)
builder.add_node("dispatcher", dispatcher_node)
builder.add_node("worker_a", worker_a_node)
builder.add_node("worker_b", worker_b_node)
builder.add_node("worker_c", worker_c_node)
builder.add_node("validator", validator_node)
builder.add_node("reviewer", reviewer_node)

# Edge'leri ekle
builder.set_entry_point("planner")
builder.add_edge("planner", "await_approval")
builder.add_conditional_edges("await_approval", route_after_approval)
builder.add_edge("dispatcher", "worker_a")  # paralel
builder.add_edge("dispatcher", "worker_b")
builder.add_edge("dispatcher", "worker_c")
builder.add_conditional_edges("worker_a", route_after_worker)
builder.add_conditional_edges("worker_b", route_after_worker)
builder.add_conditional_edges("worker_c", route_after_worker)
builder.add_edge("validator", "reviewer")
builder.add_conditional_edges("reviewer", route_after_review)

# Compile (checkpointer ile)
async with AsyncSqliteSaver.from_conn_string("./storage/graph.db") as checkpointer:
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["await_approval"]
    )
```

---

## State Tanımı

```python
# src/graph/state.py
from typing import TypedDict

class OrchestratorState(TypedDict):
    project_id: str
    project_name: str
    task_description: str

    # Dosya yönetimi (DAG)
    file_registry: dict        # {filename: "planned"|"reserved"|"in_progress"|"done"|"failed"}
    dependencies: dict         # {filename: [bağımlı_olduğu_dosyalar]}
    worker_queue: list         # [{"file": ..., "description": ..., "worker_hint": ...}]

    # Worker
    worker_status: dict        # {"worker_a": "idle"|"working"|"done"|"error"}
    worker_outputs: dict       # {"worker_a": ["file1", "file2"]}
    worker_failure_log: dict   # {"worker_a": ["görev tipi 1"]} — ContextBuilder inject eder

    # Sprint
    current_sprint: int
    sprint_type: str           # "contract" | "feature"
    sprint_status: str         # "planning"|"active"|"review"|"completed"|"failed"
    review_cycles: int

    # Onay
    awaiting_approval: bool
    approval_type: str         # "plan" | "sprint_start" | "scope_change"

    # Gemini context
    context_summary: str

    # Çıktı
    errors: list
    messages: list
```

---

## Node Yapısı

Her node: state alır, state döner. Sadece değiştirdiği alanları return eder.

```python
# src/graph/nodes/planner.py
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.context_builder import ContextBuilder
from src.core.event_bus import EventBus

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=settings.GEMINI_API_KEY
)

async def planner_node(state: OrchestratorState) -> dict:
    context = await ContextBuilder().build(state["project_id"])

    prompt = f"""
    Görev: {state['task_description']}
    Mevcut Context: {context}

    Bu proje için:
    1. Sprint tipi belirle (contract mi, feature mı?)
    2. Tüm dosya listesini üret
    3. Her dosya için bağımlılıkları belirle
    4. worker_queue'ya iş birimlerini ekle

    JSON formatında dön.
    """
    result = await llm.ainvoke(prompt)
    plan = parse_plan(result.content)

    await EventBus().emit("plan.generated", {"project_id": state["project_id"]})

    return {
        "file_registry": {f: "planned" for f in plan["files"]},
        "dependencies": plan["dependencies"],
        "worker_queue": plan["queue"],
        "sprint_type": plan["sprint_type"],
        "context_summary": context
    }
```

```python
# src/graph/nodes/worker.py
async def make_worker_node(worker_id: str, llm):
    async def worker_node(state: OrchestratorState) -> dict:
        # Bu worker'a atanmış işi bul
        my_job = next(
            (job for job in state["worker_queue"]
             if job.get("assigned_to") == worker_id),
            None
        )
        if not my_job:
            return {"worker_status": {**state["worker_status"], worker_id: "idle"}}

        filename = my_job["file"]

        # Bağımlılık kontrolü
        deps = state["dependencies"].get(filename, [])
        if not all(state["file_registry"].get(d) == "done" for d in deps):
            # Bağımlılıklar hazır değil, bekle
            return {"worker_status": {**state["worker_status"], worker_id: "waiting"}}

        # Dosyayı yaz
        try:
            code = await llm.ainvoke(my_job["description"])
            write_file(filename, code.content)

            new_registry = {**state["file_registry"], filename: "done"}
            new_outputs = {**state["worker_outputs"]}
            new_outputs.setdefault(worker_id, []).append(filename)

            await EventBus().emit("sprint.worker_done", {
                "worker_id": worker_id, "file": filename
            })

            return {
                "file_registry": new_registry,
                "worker_outputs": new_outputs,
                "worker_status": {**state["worker_status"], worker_id: "idle"}
            }
        except Exception as e:
            new_registry = {**state["file_registry"], filename: "failed"}
            return {
                "file_registry": new_registry,
                "worker_status": {**state["worker_status"], worker_id: "error"},
                "errors": state["errors"] + [{"worker": worker_id, "file": filename, "error": str(e)}]
            }

    return worker_node

# Worker'ları oluştur
worker_a_node = await make_worker_node("worker_a", ollama_llm)
worker_b_node = await make_worker_node("worker_b", openrouter_llm_1)
worker_c_node = await make_worker_node("worker_c", openrouter_llm_2)
```

---

## Koşullu Edge'ler

```python
# src/graph/edges.py

def route_after_approval(state: OrchestratorState) -> str:
    if state.get("awaiting_approval"):
        return END  # interrupt bekliyor
    return "dispatcher"

def route_after_worker(state: OrchestratorState) -> str:
    # Tüm dosyalar done veya failed mi?
    registry = state["file_registry"]
    pending = [f for f, s in registry.items() if s in ("planned", "reserved", "in_progress", "waiting")]
    if pending:
        return "dispatcher"  # Hâlâ iş var
    return "validator"       # Hepsi bitti, validate et

def route_after_review(state: OrchestratorState) -> str:
    if state["sprint_status"] == "completed":
        # Proje bitti mi?
        if all_sprints_done(state):
            return END
        return "planner"  # Sonraki sprint
    elif state["sprint_status"] == "revision_needed":
        if state["review_cycles"] >= 3:
            # Max döngü aşıldı, kullanıcıya bildir
            return "notify_user"
        return "dispatcher"  # Sadece hatalı dosyaları tekrar kuyruğa at
    return END  # failed
```

---

## Human-in-the-Loop

LangGraph `interrupt()` ile onay noktası:

```python
# src/graph/nodes/await_approval.py
from langgraph.types import interrupt

async def await_approval_node(state: OrchestratorState) -> dict:
    # EventBus'a emit et — CLI ve Telegram'ı haberdar et
    await EventBus().emit("plan.approval_needed", {
        "project_id": state["project_id"],
        "plan_summary": build_plan_summary(state),
        "thread_id": state["project_id"]  # graph resume için
    })

    # Graph burada durur, SQLite'a state kaydedilir
    decision = interrupt({
        "type": state["approval_type"],
        "project_id": state["project_id"]
    })

    # Resume edilince decision gelir: "approved" | "rejected" | "revised:<not>"
    if decision.startswith("revised:"):
        revision_note = decision.split(":", 1)[1]
        return {"awaiting_approval": False, "messages": state["messages"] + [revision_note]}

    return {"awaiting_approval": False}
```

Graph'ı resume etmek (CLI/Telegram onayı gelince):

```python
# src/core/graph_manager.py
async def resume_graph(thread_id: str, decision: str):
    config = {"configurable": {"thread_id": thread_id}}
    await graph.aupdate_state(config, {"awaiting_approval": False})
    await graph.ainvoke(Command(resume=decision), config=config)
```

---

## Crash Recovery

```python
# main.py — başlangıçta pending thread'leri resume et
async def recover_pending_graphs():
    async with AsyncSqliteSaver.from_conn_string("./storage/graph.db") as checkpointer:
        pending = await checkpointer.alist(filter={"status": "interrupted"})
        for thread in pending:
            thread_id = thread.config["configurable"]["thread_id"]
            logger.info(f"Graph resume: {thread_id}")
            await EventBus().emit("system.recovered", {
                "thread_id": thread_id,
                "message": "Sistem yeniden başladı. Onay bekleniyor."
            })
```

---

## LLM Tanımları

```python
# Gemini — planner ve reviewer
from langchain_google_genai import ChatGoogleGenerativeAI
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key=settings.GEMINI_API_KEY
)

# Worker A — Ollama (lokal)
from langchain_community.chat_models import ChatOllama
ollama_llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_HOST
)

# Worker B — OpenRouter
from langchain_openai import ChatOpenAI
openrouter_llm_1 = ChatOpenAI(
    model=settings.OPENROUTER_MODEL_1,
    api_key=settings.OPENROUTER_API_KEY_1,
    base_url="https://openrouter.ai/api/v1"
)

# Worker C — OpenRouter
openrouter_llm_2 = ChatOpenAI(
    model=settings.OPENROUTER_MODEL_2,
    api_key=settings.OPENROUTER_API_KEY_2,
    base_url="https://openrouter.ai/api/v1"
)
```

---

## Kritik Kurallar

- Her node async fonksiyon olmalı, state alır dict döner (sadece değiştirilen alanlar)
- Node'lar EventBus import edebilir ama interface'leri (Telegram, CLI) direkt çağıramaz
- Tüm LLM çağrıları `await llm.ainvoke()` — blocking çağrı yasak
- `interrupt()` sadece onay noktalarında kullanılır, diğer bekleme senaryolarında kullanılmaz
- Graph compile edilirken `interrupt_before=["await_approval"]` zorunlu
- Worker node'lar `file_registry`'de "done" olmayan bağımlılığa sahip dosyayı işlemez
- Review döngüsü max 3 — aşılırsa `route_after_review` kullanıcı bildirim node'una yönlendirir
- Her `graph.ainvoke()` çağrısına `{"configurable": {"thread_id": project_id}}` config eklenir
- `@human_feedback` decorator kullanılmaz

---

## Contract Sprint Kuralı

Her projenin **ilk sprinti** contract sprint olmak zorunda:
- Planner node sprint_type = "contract" döner
- Contract sprint çıktıları: API şeması, shared types, klasör yapısı, dosya listesi
- Feature sprint'ler contract sprint tamamlanmadan başlamaz (edge kontrolü)
- Contract dosyaları `file_registry`'de "contract" flag'i taşır, worker'lar silip değiştiremez

---

## References

- LangGraph docs: https://langchain-ai.github.io/langgraph/
- `project-architecture/SKILL.md` — OrchestratorState şeması, EventBus events, dosya sınırları
- `python-async-patterns/SKILL.md` — async kurallar, EventBus implementasyonu
