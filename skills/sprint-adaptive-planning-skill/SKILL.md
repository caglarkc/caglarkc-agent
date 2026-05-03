---
name: sprint-adaptive-planning
description: Planner AI için — sprint sırasında gelen yeni bilgiye göre planı dinamik olarak güncellemek; sabit plan yerine uyarlanabilir yaklaşım.
---

## Purpose

Sabit plan gerçeklikle çakışır — bir görev beklenenden uzun sürer.
Adaptif planlama: ilerleme verilerine göre kalan görevleri yeniden önceliklendirir.
Kalan süre ve başarı oranına göre planı küçültür veya genişletir.

---

## When to Apply

- Sprint yarısında gerçek ilerleme tahminle uyuşmadığında
- Bir görev çok uzun sürdüğünde diğerlerini etkiliyor
- Yeni bilgi (hata, bağımlılık) plan varsayımlarını geçersiz kıldığında

---

## Rules

- Yeniden planlama: her %25 ilerlemede otomatik değerlendirme.
- Kısaltma: tahminden %50 geride kalınırsa düşük öncelikli görevler ertelenir.
- Genişletme: beklenenden hızlıysa backlog'dan görev eklenir.
- Değişiklik: kullanıcıya bildirilir.

---

## Guidelines

```python
from datetime import datetime

def evaluate_sprint_progress(state: dict) -> dict:
    tasks   = state.get("tasks", [])
    total   = len(tasks)
    done    = sum(1 for t in tasks if t.get("status") == "done")
    pct     = done / total if total else 0

    started  = state.get("sprint_started_at")
    if not started:
        return {}
    elapsed  = (datetime.utcnow() - datetime.fromisoformat(started)).total_seconds() / 60
    capacity = state.get("sprint_minutes", 60)
    time_pct = elapsed / capacity if capacity else 0

    velocity_ratio = pct / time_pct if time_pct > 0 else 1.0
    return {
        "completion_pct": round(pct * 100, 1),
        "time_used_pct":  round(time_pct * 100, 1),
        "velocity_ratio": round(velocity_ratio, 2),
    }

def adapt_plan(state: dict, evaluation: dict) -> dict:
    ratio = evaluation.get("velocity_ratio", 1.0)
    if ratio >= 1.2:
        # Hızlıyız — backlog'dan görev ekle
        backlog = list(state.get("backlog", []))
        if backlog:
            next_item = backlog.pop(0)
            return {"backlog": backlog, "adaptation": f"Backlog'dan eklendi: {next_item}"}
    elif ratio < 0.5:
        # Yavaşız — düşük öncelikli görevleri ertele
        tasks    = list(state.get("tasks", []))
        deferred = 0
        for t in tasks:
            if t.get("status") == "planned" and t.get("priority", 3) >= 4:
                t["status"] = "deferred"
                deferred += 1
        return {"tasks": tasks, "adaptation": f"{deferred} düşük öncelikli görev ertelendi"}
    return {}
```

---

## References

- `sprint-feedback-loop-skill/SKILL.md` — geri besleme döngüsü
- `sprint-capacity-planning-skill/SKILL.md` — kapasite planlaması
- `sprint-scope-creep-detection-skill/SKILL.md` — kapsam kayması
