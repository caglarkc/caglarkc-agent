---
name: sprint-budget-estimation
description: Planner AI için — bir sprint'in tahmini süresini ve karmaşıklığını değerlendirmek; kullanıcıya gerçekçi beklenti sunmak.
---

## Purpose

Kullanıcı "3 saatte biter mi?" diye sorarsa gerçekçi cevap verilmeli.
Sprint büyüklüğü (görev sayısı, dosya sayısı) zaman tahminine çevrilir.
Aşırı vaatte bulunmak güven kaybettirir.

---

## When to Apply

- Sprint planı kullanıcıya sunulmadan önce
- Çok büyük sprint önerilmeden önce
- Kullanıcı süre sorarken

---

## Rules

- Karmaşıklık tahmini: basit / orta / karmaşık.
- Tahmini süre: görev başına sabit dakika değil, göreceli.
- "Kesin süre" verilmez — "yaklaşık X-Y görev" söylenir.
- Büyük sprint: >8 görev → ikiye bölme önerilir.

---

## Guidelines

Karmaşıklık matrisi:
```
Basit:    1-3 görev, mevcut modüle ekleme, test gerektirmez
          → "Birkaç saatte tamamlanabilir"

Orta:     4-7 görev, yeni modül, test gerekli
          → "Yarım ila tam gün"

Karmaşık: 8+ görev, mimari değişiklik, integration
          → "2-3 gün veya sprint bölünmeli"
```

```python
def estimate_sprint_complexity(tasks: list[dict]) -> str:
    task_count = len(tasks)
    total_files = sum(len(t.get("files", [])) for t in tasks)
    has_new_module = any(
        "new" in t.get("description", "").lower()
        for t in tasks
    )
    
    if task_count <= 3 and total_files <= 5:
        return "basit"
    elif task_count <= 7 and total_files <= 15:
        return "orta"
    else:
        return "karmaşık"
```

PM'in sunum formatı:
```
[PLANLAMA] Sprint değerlendirmesi:

Görev sayısı: 5
Etkilenen dosya: 8
Karmaşıklık: Orta

Tahmini süre: Sprint normal hızda yaklaşık yarım gün sürer.
Büyük sprint değil — aynen devam edebiliriz.
```

---

## References

- `sprint-task-decomposition-skill/SKILL.md` — görev ayrıştırma
- `scope-boundary-detection-skill/SKILL.md` — kapsam sınırı
- `sprint-summary-generation-skill/SKILL.md` — özet
