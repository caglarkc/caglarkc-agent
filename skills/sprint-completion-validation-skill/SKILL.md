---
name: sprint-completion-validation
description: Planner AI için — bir sprint'in gerçekten tamamlanıp tamamlanmadığını doğrulamak; tüm dosyaların yazıldığını, validation geçtiğini ve bir sonraki sprint'e geçilebileceğini kontrol etmek.
---

## Purpose

Eksik tamamlanmış sprint'in "completed" olarak işaretlenmesini engeller.
Tüm dosyalar yazılmış ama bazıları validate olmamışsa sprint bitmemiştir.
Bir sonraki sprint'in doğru zemin üzerine inşa edilmesini garantiler.

---

## When to Apply

- Reviewer node'da sprint tamamlanma kararı verilirken
- `sprint.completed` event'i emit edilmeden önce
- Kullanıcıya "Sprint bitti" bildirilmeden önce

---

## Rules

- Sprint tamamlandı sayılır sadece şu koşullarda:
  1. `file_registry`'deki tüm dosyalar `done` statüsünde.
  2. `validation_issues` listesi boş veya sadece warning içeriyor.
  3. `worker_queue`'da `planned` veya `in_progress` görev kalmadı.
- Tek dosya `failed` → sprint `failed`.
- Kısmen tamamlanmış sprint bir sonraki sprint'in başlangıcı değildir.
- Tamamlanan dosyalar ve yazılmayan dosyalar ayrı ayrı raporlanır.

---

## Guidelines

Completion check:
```python
def is_sprint_complete(state: OrchestratorState) -> bool:
    # 1. Tüm dosyalar done mu?
    all_done = all(
        status == "done"
        for status in state.get("file_registry", {}).values()
    )
    
    # 2. Aktif görev var mı?
    pending_tasks = [
        q for q in state.get("worker_queue", [])
        if q["status"] in ("planned", "in_progress")
    ]
    
    # 3. Kritik validation hatası var mı?
    critical_issues = [
        i for i in state.get("validation_issues", [])
        if i.get("severity") == "error"
    ]
    
    return all_done and not pending_tasks and not critical_issues
```

Sprint tamamlanma raporu:
```
SPRINT TAMAMLANDI ✓

Yazılan dosyalar (5/5):
✓ src/graph/nodes/planner.py
✓ src/core/manager_planning.py
✓ src/graph/state.py
✓ src/storage/models.py
✓ tests/test_planner.py

Validation: 0 hata, 2 uyarı (non-critical)
Süre: 47 dakika
```

---

## References

- `review-cycle-limit-enforcement-skill/SKILL.md` — döngü limiti
- `acceptance-criteria-definition-skill/SKILL.md` — başarı kriterleri
- `file-status-state-machine-skill/SKILL.md` — dosya durumları
