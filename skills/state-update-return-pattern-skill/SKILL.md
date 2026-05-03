---
name: state-update-return-pattern
description: Coder AI için — LangGraph node'larının sadece değişen state alanlarını döndürme pattern'ı; tam state kopyalama ve mutation'dan kaçınma.
---

## Purpose

LangGraph'ta node'ların sadece değişen alanları döndürmesi gerekir.
Tam state döndürmek gereksiz override'a ve reducer bypass'a yol açar.
State mutation (state["key"] = value) checkpoint'e yansımaz.

---

## When to Apply

- Node fonksiyonu `return` ifadesi yazılırken
- State alanı güncellenmesi gerektiğinde
- Liste veya dict alanına eleman eklenirken

---

## Rules

- Node sadece değişen alanların dict'ini döndürür.
- Değişmeyen alanlar döndürülmez.
- State mutasyonu yasak: `state["key"] = value` yazmak checkpoint'e yansımaz.
- Liste append: `state.get("list", []) + [new_item]` (yeni liste).
- Dict update: `{**state.get("dict", {}), "key": value}` (yeni dict).
- Reducer'lı alan (`Annotated[list, add]`): sadece yeni elemanlar döndürülür.

---

## Guidelines

Doğru güncelleme pattern'ları:
```python
# Skaler değer güncelleme
return {"draft_plan": new_plan}

# Liste'ye eleman ekleme (yeni liste)
return {
    "messages": state.get("messages", []) + ["Yeni mesaj"],
    "errors": state.get("errors", []) + [{"node": "x", "error": str(e)}]
}

# Dict güncelleme (yeni dict)
current_registry = state.get("file_registry", {})
return {
    "file_registry": {**current_registry, "src/new.py": "done"}
}

# Worker status güncelleme
current_status = state.get("worker_status", {})
return {
    "worker_status": {**current_status, "worker_a": "working"}
}

# Sayaç artırma
return {
    "review_cycles": state.get("review_cycles", 0) + 1
}
```

Yanlış pattern'lar:
```python
# YANLIŞ — mutation
state["draft_plan"] = new_plan  # checkpoint'e yansımaz
return state  # tüm state döndürülüyor

# YANLIŞ — tam state döndürme
new_state = dict(state)
new_state["draft_plan"] = new_plan
return new_state  # reducer'lı alanlar override edilir
```

Reducer'lı alan için:
```python
# Annotated[list[str], add] olan messages için
# Sadece yeni mesajları döndür, mevcut liste otomatik birleşir
return {"messages": ["Bu mesaj mevcut listeye eklenir"]}
```

---

## References

- `node-function-signature-skill/SKILL.md` — node imzası
- `state-typeddict-definition-skill/SKILL.md` — reducer tanımı
- `langgraph-patterns-skill/SKILL.md` — LangGraph kuralları
