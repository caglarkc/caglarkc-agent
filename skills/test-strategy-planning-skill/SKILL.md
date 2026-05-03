---
name: test-strategy-planning
description: Planner AI için — bir sprint için hangi testlerin yazılacağına karar vermek; unit, integration ve smoke test ihtiyaçlarını belirlemek.
---

## Purpose

Her sprint için doğru test kapsamını planlar.
Test olmayan kritik kod başarısız review'a yol açar.
Gereksiz test de sprint'i uzatır — doğru dengeyi kurar.

---

## When to Apply

- Sprint planlanırken test görevi eklenip eklenmeyeceğine karar verilirken
- Review sırasında test coverage değerlendirilirken
- Yeni node veya servis eklenirken

---

## Rules

- Her yeni node için: en az 1 birim test (happy path + 1 hata senaryosu).
- Repository metodu: DB mock veya tmp_path fixture ile test.
- LLM çağrısı: mutlaka mock — gerçek API çağrısı değil.
- Event emit: mock event bus ile doğrulama.
- Integration test: kritik akışlar için (planner → dispatcher → worker).
- Test dosyası ayrı görev olarak planlanır — implementation'dan sonra.

---

## Guidelines

Test öncelik listesi (bu proje için):

**Mutlaka test edilmeli:**
- LangGraph node'ları (izole birim test)
- Provider fallback zinciri (mock ile)
- Retry decorator (backoff doğrulaması)
- Approval/rejection akışı
- Recovery mantığı (partial state)

**Test edilmeli:**
- Repository metodları (tmp_path DB ile)
- Event emit/subscribe doğrulama
- Settings validation (zorunlu alan eksikse hata)

**Opsiyonel (zaman varsa):**
- Telegram handler'ları
- CLI komut parser
- Full integration (gerçek graph)

Sprint test plan formatı:
```
SPRINT X TEST PLANI:

Birim testler:
- tests/test_nodes/test_planner_node.py — planner happy path + LLM error
- tests/test_core/test_retry.py — backoff hesaplama, max retry

Integration test:
- tests/test_integration/test_plan_flow.py — planner → dispatcher mock akışı

Atlanabilir:
- Telegram mock test (ayrı sprint)
```

---

## References

- `acceptance-criteria-definition-skill/SKILL.md` — test kriterleri
- `pytest-async-test-skill/SKILL.md` — test yazma
- `graph-node-isolation-test-skill/SKILL.md` — node testi
