---
name: proto-typing
description: Coder AI için — tam implementasyon öncesinde hızlı çalışan prototip yazmak; doğrulama sonrası production kalitesine yükseltmek.
---

## Purpose

Tam implementasyon yazmadan önce yaklaşımın doğruluğunu kanıtlamak istersin.
Prototip: minimal kod, hard-coded değerler, mock veriler — ama çalışan.
Kullanıcı onayı sonrası prototip production koduna dönüştürülür.

---

## When to Apply

- Yeni LangGraph akışı test edilirken
- Bilinmeyen LLM entegrasyonu denenirken
- "Bu çalışır mı?" sorusu cevaplanırken

---

## Rules

- Prototip: `# PROTOTYPE` yorumuyla işaretlenir.
- Hard-coded değer kabul edilir — prototipte sorun değil.
- Test olmadan geçebilir — prototip doğrulama aşamasında.
- Production'a geçerken: yorumlar silinir, değerler config'e taşınır.
- Prototip dosyaları: `prototypes/` dizinine konulur.

---

## Guidelines

```python
# PROTOTYPE: LangGraph checkpoint entegrasyonu test

# Hard-coded değerler — production'da Settings'ten alınacak
DB_PATH = "/tmp/proto_checkpoint.db"
PROJECT_ID = "proto-test"

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from typing import TypedDict

class ProtoState(TypedDict):
    counter: int
    messages: list[str]

def increment_node(state: ProtoState) -> ProtoState:
    return {
        "counter": state["counter"] + 1,
        "messages": state["messages"] + [f"step {state['counter']}"],
    }

# Graph kur
builder = StateGraph(ProtoState)
builder.add_node("inc", increment_node)
builder.add_edge(START, "inc")
builder.add_edge("inc", END)

async def run_prototype():
    checkpointer = AsyncSqliteSaver.from_conn_string(DB_PATH)
    graph = builder.compile(checkpointer=checkpointer)
    
    config = {"configurable": {"thread_id": PROJECT_ID}}
    result = await graph.ainvoke({"counter": 0, "messages": []}, config)
    print(f"Sonuç: {result}")
    
    # Resume test
    result2 = await graph.ainvoke(None, config)
    print(f"Resume: {result2}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_prototype())
```

Production'a geçiş checklist:
```
☐ Hard-coded değerler → Settings
☐ PROTOTYPE yorumları → silinir
☐ Hata yönetimi eklenir
☐ Testler yazılır
☐ Dosya prototypes/'dan src/'a taşınır
```

---

## References

- `graph-assembly-skill/SKILL.md` — graph oluşturma
- `integration-test-setup-skill/SKILL.md` — test
- `schema-first-design-skill/SKILL.md` — tasarım önce
