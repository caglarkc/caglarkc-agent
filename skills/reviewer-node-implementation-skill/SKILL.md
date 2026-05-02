---
name: reviewer-node-implementation
description: Coder AI için — LangGraph reviewer node'unu implemente etmek; üretilen kodu LLM ile değerlendirerek geç/kalma kararı vermek.
---

## Purpose

Reviewer node, worker'ın ürettiği kodu standartlara göre değerlendirir.
LLM reviewer rolüyle kodu inceler, sorunları listeler.
Onaylarsa sprint devam eder; reddederse worker yeniden çalışır.

---

## When to Apply

- `src/graph/nodes/reviewer.py` yazılırken
- Kod kalite kontrolü pipeline'a eklenirken
- Review döngüsü sınırı implemente edilirken

---

## Rules

- Reviewer LLM çağrısı: mock'lanabilir olmalı (test için).
- Max review döngüsü: 3 — aşılırsa zorla `approved` yapılır.
- Review sonucu state'e yazılır: `review_result = "approved" | "rejected"`.
- Reddetme sebebi: `review_comments` listesine eklenir.

---

## Guidelines

```python
# src/graph/nodes/reviewer.py
from langchain_core.messages import SystemMessage, HumanMessage

REVIEWER_SYSTEM = """Sen bir kıdemli Python geliştiricisisin.
Verilen kodu incele ve şu kriterleri değerlendir:
1. Syntax ve import doğruluğu
2. Async/await kullanımı
3. Hata yönetimi
4. Type hint'ler
5. Güvenlik (hard-coded secret yok)

Cevabın JSON formatında olmalı:
{"approved": true/false, "issues": ["...", "..."]}
"""

async def reviewer_node(state: OrchestratorState) -> OrchestratorState:
    review_count = state.get("review_count", 0)
    
    # Max döngü kontrolü
    if review_count >= 3:
        logger.warning("Max review döngüsü aşıldı, zorla onaylanıyor")
        return {"review_result": "approved", "review_count": review_count + 1}
    
    # Son üretilen dosyaları al
    recent_files = _get_recent_files(state)
    code_content = _read_file_contents(recent_files)
    
    response = await llm.ainvoke([
        SystemMessage(content=REVIEWER_SYSTEM),
        HumanMessage(content=f"İncelenecek kod:\n{code_content}"),
    ])
    
    result = parse_review_response(response.content)
    
    return {
        "review_result": "approved" if result.approved else "rejected",
        "review_comments": result.issues,
        "review_count": review_count + 1,
    }
```

Graph edge yönlendirme:
```python
def route_after_review(state: OrchestratorState) -> str:
    if state.get("review_result") == "approved":
        return "done"
    return "worker"   # yeniden çalıştır
```

---

## References

- `review-cycle-limit-enforcement-skill/SKILL.md` — döngü limiti
- `code-review-checklist-skill/SKILL.md` — review kriterleri
- `node-function-signature-skill/SKILL.md` — node imzası
