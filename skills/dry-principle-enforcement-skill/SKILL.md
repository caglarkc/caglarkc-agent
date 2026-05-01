---
name: dry-principle-enforcement
description: Coder AI için — tekrar eden kod bloklarını tespit etmek ve ortak fonksiyon/yardımcı modüle taşımak; "Don't Repeat Yourself" prensibini uygulamak.
---

## Purpose

Aynı mantığın birden fazla yerde yazılmasını önler.
Değişiklik tek yerde yapılarak tüm kullanım noktaları güncellenir.
Copy-paste kod hata ayıklamayı zorlaştırır.

---

## When to Apply

- Aynı kod bloğu 3 veya daha fazla yerde görüldüğünde
- Aynı mantık farklı node'larda tekrar yazıldığında
- Helper fonksiyon çıkartılabilecek durum fark edildiğinde

---

## Rules

- 3 tekrar → yardımcı fonksiyon çıkar.
- Node'larda ortak mantık → `src/core/` servis metoduna taşı.
- Sabit string veya değer → isimlendirilmiş sabit.
- Aynı Pydantic model birden fazla yerde tanımlanmış → tek model.
- Test yardımcıları → `tests/helpers/` dizinine taşı.

---

## Guidelines

DRY ihlali tespiti:
```python
# YANLIŞ — 3 node'da aynı hata kayıt kodu
# planner.py:
return {"errors": state.get("errors", []) + [{"node": "planner", "error": str(e)}]}
# dispatcher.py:
return {"errors": state.get("errors", []) + [{"node": "dispatcher", "error": str(e)}]}
# worker.py:
return {"errors": state.get("errors", []) + [{"node": "worker", "error": str(e)}]}

# DOĞRU — yardımcı fonksiyon
# src/graph/utils.py
def append_error(state: OrchestratorState, node: str, error: Exception) -> dict:
    return {
        "errors": state.get("errors", []) + [{
            "node": node,
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

# planner.py:
return append_error(state, "planner", e)
# dispatcher.py:
return append_error(state, "dispatcher", e)
```

Ortak yardımcı fonksiyonlar için yer:
```
src/graph/utils.py     — node yardımcıları
src/core/helpers.py    — genel servis yardımcıları
tests/helpers/         — test yardımcıları
```

---

## References

- `single-responsibility-enforcement-skill/SKILL.md` — sorumluluk
- `function-length-review-skill/SKILL.md` — fonksiyon boyutu
- `dead-code-detection-skill/SKILL.md` — kullanılmayan kod
