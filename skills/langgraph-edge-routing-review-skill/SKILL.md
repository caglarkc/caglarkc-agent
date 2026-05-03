---
name: langgraph-edge-routing-review
description: Planner AI için — LangGraph conditional edge fonksiyonlarının doğru state'e göre routing yaptığını, tüm olası sonuçların ele alındığını ve sonsuz döngü oluşturmadığını review sırasında doğrulamak.
---

## Purpose

Graph'ın her durumda doğru node'a gittiğini garantiler.
Eksik routing case'lerini yakalar (unhandled state → graph donabilir).
Sonsuz döngü oluşturabilecek edge bağlantılarını tespit eder.

---

## When to Apply

- `src/graph/edges.py` review edilirken
- Yeni conditional edge eklenirken
- Graph akışı değiştirilirken
- "Graph neden burada takılı kalıyor?" soruşturulurken

---

## Rules

- Her routing fonksiyonu string döndürür (node adı veya "END").
- Tüm olası state kombinasyonları ele alınmalı — `else` veya default case zorunlu.
- Döngüsel routing: A→B→A izin verilir ama maksimum cycle sayısı kontrol edilmeli.
- Routing fonksiyonu state'i okur ama değiştirmez (pure function).
- Review cycle sayısı `review_cycles` alanıyla takip edilmeli, maksimum aşılırsa END.

---

## Guidelines

Edge fonksiyon kontrol:
```python
# DOĞRU — tüm case'ler ele alınmış
def route_after_planner(state: OrchestratorState) -> str:
    if state.get("approval_request"):
        return END  # onay bekleniyor
    if state.get("draft_plan"):
        return "dispatcher"
    return END  # default: bitir (eksik plan durumu)

# YANLIŞ — default case yok
def route_after_planner(state: OrchestratorState) -> str:
    if state.get("approval_request"):
        return END
    # draft_plan yoksa → None döner → graph error!
```

Döngü sayacı kontrolü:
```python
# Reviewer → Dispatcher döngüsü
def route_after_reviewer(state: OrchestratorState) -> str:
    if state.get("review_cycles", 0) >= 3:
        return END  # maksimum döngü aşıldı
    if state.get("needs_revision"):
        return "dispatcher"
    return END
```

Graph akış doğrulama:
```
planner → (onay varsa) END
planner → (onay yoksa) dispatcher
dispatcher → (iş varsa) worker
dispatcher → (iş yoksa) reviewer
worker → executor
executor → validator
validator → (sorun varsa) reviewer
validator → (sorun yoksa) dispatcher veya reviewer
reviewer → (revizyon varsa) dispatcher
reviewer → (tamam) END
```

---

## References

- `langgraph-node-design-review-skill/SKILL.md` — node tasarımı
- `review-cycle-limit-enforcement-skill/SKILL.md` — döngü limiti
- `langgraph-patterns-skill/SKILL.md` — LangGraph referans
