---
name: function-length-review
description: Planner AI için — çok uzun fonksiyonları tespit etmek; tek sorumluluktan sapan ve yeniden kullanılabilir parçalara bölünmesi gereken fonksiyonları işaretlemek.
---

## Purpose

Aşırı uzun fonksiyonları review sırasında yakalar.
Uzun fonksiyon = birden fazla sorumluluk = zor test edilir, zor anlaşılır.
Coder AI'ı makul boyutlarda, odaklı fonksiyonlar yazmaya yönlendirir.

---

## When to Apply

- 40 satırdan uzun herhangi bir fonksiyon görüldüğünde
- Fonksiyon içinde "bölüm" yorumları varsa (# Adım 1, # Bölüm 2)
- Tek fonksiyonda 3'ten fazla farklı şey yapılıyorsa

---

## Rules

- Soft limit: 30 satır. Hard limit: 50 satır (test edilebilirlik için).
- Fonksiyon içinde "bölüm" yorumu: yardımcı fonksiyon çıkarılmalı.
- 3+ seviye nested if/for: karmaşıklık yüksek, bölünmeli.
- LangGraph node'ları: node fonksiyonu ince wrapper, iş mantığı yardımcı fonksiyonlarda.
- Node'da 10+ satır iş mantığı varsa servis metoduna taşınmalı.

---

## Guidelines

Bölme stratejisi:
```python
# YANLIŞ — tek devasa fonksiyon
async def planner_node(state: OrchestratorState) -> dict:
    # Step 1: history oluştur
    history = []
    for msg in state.get("conversation_history", []):
        ...  # 15 satır
    
    # Step 2: LLM çağır
    response = await llm.invoke(...)  # 10 satır
    
    # Step 3: plan parse et
    plan = {}
    for item in response.content:
        ...  # 20 satır
    
    # Step 4: queue oluştur
    queue = []
    ...  # 15 satır
    
    return {...}  # Toplam: 60+ satır

# DOĞRU — ince wrapper + yardımcı fonksiyonlar
async def planner_node(state: OrchestratorState) -> dict:
    history = _build_history(state)
    response = await _invoke_llm(history, state["task_description"])
    plan = _parse_plan(response)
    queue = _build_queue(plan)
    return {"draft_plan": plan, "worker_queue": queue}

def _build_history(state: OrchestratorState) -> list:
    ...  # 15 satır — izole test edilebilir

async def _invoke_llm(history: list, task: str) -> dict:
    ...  # 10 satır

def _parse_plan(response: dict) -> dict:
    ...  # 20 satır

def _build_queue(plan: dict) -> list[QueueEntry]:
    ...  # 15 satır
```

---

## References

- `single-responsibility-enforcement-skill/SKILL.md` — tek sorumluluk
- `cognitive-complexity-review-skill/SKILL.md` — karmaşıklık azaltma
- `langgraph-node-design-review-skill/SKILL.md` — node tasarımı
