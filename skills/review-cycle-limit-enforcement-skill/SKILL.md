---
name: review-cycle-limit-enforcement
description: Planner AI için — reviewer → dispatcher döngüsünün sonsuz tekrarlamasını engellemek; maksimum review cycle sayısını aşınca sprint'i başarısız olarak işaretlemek.
---

## Purpose

Sonsuz review döngüsünü engeller.
Sistematik hata durumunda reviewer defalarca aynı sorunu tespit eder ve dispatcher'a gönderir — çıkış olmaz.
Maksimum cycle sayısına ulaşıldığında graceful failure uygulanır.

---

## When to Apply

- `route_after_reviewer()` edge fonksiyonunda
- Reviewer node'da karar verilirken
- Sprint başarısız olarak işaretlenirken

---

## Rules

- Maksimum review cycle: 3 (konfigüre edilebilir).
- `review_cycles` sayacı her reviewer → dispatcher geçişinde artırılır.
- Limit aşılınca: sprint `failed` olarak işaretlenir.
- Kullanıcıya: hangi dosyada sorun var, ne denemeler yapıldı bilgisi verilir.
- Limit aşıldıktan sonra insan müdahalesi istenir.

---

## Guidelines

Review cycle sayacı:
```python
# reviewer node içinde
current_cycles = state.get("review_cycles", 0)

if needs_revision:
    if current_cycles >= MAX_REVIEW_CYCLES:
        # limit aşıldı → fail
        return {
            "review_cycles": current_cycles + 1,
            "errors": state.get("errors", []) + [{
                "type": "max_review_cycles",
                "message": f"Sprint {MAX_REVIEW_CYCLES} review'dan sonra tamamlanamadı",
                "failed_files": get_failed_files(state)
            }]
        }
    else:
        # tekrar dene
        return {
            "review_cycles": current_cycles + 1,
            "needs_revision": True
        }
```

Edge routing:
```python
def route_after_reviewer(state: OrchestratorState) -> str:
    if state.get("review_cycles", 0) >= MAX_REVIEW_CYCLES:
        return END  # zorla bitir
    if state.get("needs_revision"):
        return "dispatcher"
    return END
```

Kullanıcı bildirimi (limit aşılınca):
```
[REVIEW] Sprint başarısız: 3 deneme sonucu düzeltilemedi.

Sorunlu dosyalar:
• src/graph/nodes/worker.py — async pattern hatası (3 kez tekrar etti)

Manuel inceleme gerekiyor. /inspect worker.py ile inceleyebilirsiniz.
```

---

## References

- `langgraph-edge-routing-review-skill/SKILL.md` — edge routing
- `worker-failure-triage-skill/SKILL.md` — hata analizi
- `sprint-completion-validation-skill/SKILL.md` — sprint tamamlanma
