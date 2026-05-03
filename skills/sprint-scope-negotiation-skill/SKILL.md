---
name: sprint-scope-negotiation
description: Planner AI için — sprint kapsamı konusunda kullanıcıyla müzakere etmek; çok büyük isteği bölerek veya küçük isteği zenginleştirerek doğru boyuta getirmek.
---

## Purpose

Kullanıcının istediği her şeyi tek sprint'e sığdırmak bazen mümkün değil.
Müzakere: neleri şimdi, neleri sonraki sprint'te yapacağımıza birlikte karar verilir.
Aşırı kısıtlama da sorun — kullanıcının gerçek değer beklentisi karşılanmalı.

---

## When to Apply

- Sprint büyüklüğü "çok büyük" kategori taşıdığında
- Kullanıcı tek sprint'e aşırı özellik sığdırmak istediğinde
- Kullanıcı "az" dediğinde gerçekten az mı yoksa MVP mi istediği net değilken

---

## Rules

- Müzakere: seçenekler sunulur — dayatma yapılmaz.
- Seçenek 1: tüm istek + sprint bölünmesi.
- Seçenek 2: MVP + sonraki sprint listesi.
- Seçenek 3: kullanıcının tercih ettiği kapsam.
- Karar kullanıcıya ait — PM öneri yapar.

---

## Guidelines

PM müzakere formatı:
```
[PLANLAMA] İsteğinizi değerlendirdim.

Tüm özellikleri tek sprint'e sığdırmak zor:
→ 12 görev, 18 dosya — önerilen maksimum 8 görev.

3 seçenek:

Seçenek A: Temel özellikler şimdi (Sprint 1)
  - Core modeller ve repository
  - Temel LangGraph graph
  → Sonraki sprint: Telegram + CLI

Seçenek B: Her şeyi 2 sprint'e böl
  - Sprint 1: Altyapı
  - Sprint 2: Arayüz

Seçenek C: Kendi önceliğinizi belirleyin
  (Hangi özellikler kesinlikle bu sprint'te olmalı?)

Ne tercih edersiniz?
```

```python
def suggest_scope_split(
    tasks: list[dict],
    max_per_sprint: int = 8,
) -> tuple[list[dict], list[dict]]:
    """Görevleri iki gruba böler: şimdi ve sonra."""
    if len(tasks) <= max_per_sprint:
        return tasks, []
    
    # Bağımlılığı olmayan görevler önce
    primary = [t for t in tasks if not t.get("depends_on")][:max_per_sprint]
    secondary = [t for t in tasks if t not in primary]
    
    return primary, secondary
```

---

## References

- `sprint-budget-estimation-skill/SKILL.md` — büyüklük tahmini
- `feature-breakdown-skill/SKILL.md` — özellik ayrıştırma
- `mvp-identification-skill/SKILL.md` — MVP tespiti
