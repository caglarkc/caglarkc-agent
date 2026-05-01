---
name: scope-boundary-detection
description: Planner AI için — bir isteğin neyi kapsadığını ve neyi kapsamadığını net olarak tanımlamak; scope creep ve belirsiz genişlemeyi engellemek.
---

## Purpose

Her sprint ve görevin sınırlarını netleştirir.
"Bu iş nerede başlar, nerede biter?" sorusunu yanıtlar.
Scope dışı talepleri tespit eder ve kullanıcıya bildirir.

---

## When to Apply

- Yeni bir sprint planlanmaya başlandığında
- Kullanıcı mevcut bir göreve yeni şeyler eklemeye başladığında
- Bir görev açıklaması birden fazla farklı işi içeriyorsa
- Worker'a verilecek görev yazılmadan önce

---

## Rules

- Her sprint için "IN scope / OUT scope" listesi yapılır.
- Scope dışı talep tespit edilirse kullanıcıya bildirilir, mevcut sprinte eklenmez — yeni sprint olarak planlanır.
- Bir worker'ın sorumluluğu maksimum 3 dosyayla sınırlı tutulur.
- "Sonradan ekleriz" yaklaşımı yasak — ya şimdi scope'a girer, ya ayrı iş olur.
- Teknik borç scope dışına çıkarılır, ayrı `[GÖREV]` olarak planlanır.

---

## Guidelines

Scope sınırı çizme adımları:
1. İsteği tek cümleyle özetle.
2. Bu iş için hangi dosyalar/modüller **mutlaka** değişmeli? → IN
3. Değişebilir ama bu sprintte değişmemeli olanlar? → OUT (sonraki sprint)
4. Hiç değişmemeli olanlar? → YASAK (mimari koruma)

Sınır işaretleme formatı:
```
IN SCOPE:
- src/graph/nodes/planner.py — plan üretim mantığı
- src/core/manager_planning.py — LLM çağrısı

OUT SCOPE (bu sprint):
- src/interfaces/telegram/ — ayrı sprint
- src/storage/repository.py — dokunulmaz

YASAK:
- src/graph/state.py — state schema değişikliği ayrı onay gerektirir
```

---

## Examples

```
Kullanıcı: "Telegram'a bildirim ekle ve aynı zamanda planner'ı da iyileştir"

Tespit: 2 farklı scope var.

Sprint A: Telegram bildirim (src/interfaces/telegram/)
Sprint B: Planner iyileştirme (src/graph/nodes/planner.py)

[ONAY-BEKLE] Bu iki ayrı sprint olarak mı ilerleyelim?
```

---

## References

- `pm-mode-skill/SKILL.md` — sprint planlama workflow
- `sprint-type-selection-skill/SKILL.md` — sprint türü seçimi
- `project-architecture-skill/SKILL.md` — modül sınırları
