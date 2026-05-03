---
name: schema-first-design
description: Coder AI için — implementasyona başlamadan önce Pydantic modelleri ve DB şemasını tasarlamak; kontrat önce, implementasyon sonra.
---

## Purpose

Implementasyon önce başlarsa ortada şema değişikliği gerekir — tüm kod yeniden yazılır.
Schema-first: önce model, sonra repository, sonra servis, sonra node.
Şema değişmeden implementasyon stabil kalır.

---

## When to Apply

- Yeni modül tasarlanmadan önce
- Planner yeni sprint için görev sırası belirlerken
- DB tablosu tasarımı aşamasında

---

## Rules

- Sprint sırası: model → DB şema → repository → servis → node → test.
- Model tasarımı kod yazmadan önce onaylanır (opsiyonel).
- DB şema: migration olarak yazılır.
- Model değişikliği: tüm bağımlı kod güncellenir.

---

## Guidelines

Şema-first sprint sırası:
```
Görev 1: Pydantic modelleri (src/storage/models.py)
  - Sprint, Project, Task, Decision
  - Zorunlu alanlar, tipler, validation

Görev 2: DB şeması migration (src/storage/migrations.py)
  - CREATE TABLE SQL
  - index tanımları

Görev 3: Repository (src/storage/repository.py)
  - CRUD operasyonları
  - Görev 1 ve 2'ye bağımlı

Görev 4: Servis (src/core/sprint_service.py)
  - İş mantığı
  - Görev 3'e bağımlı

Görev 5: Node (src/graph/nodes/planner.py)
  - Görev 4'e bağımlı

Görev 6: Testler
  - Tüm görevlere bağımlı
```

```python
# Şema doğrulama — implementasyon başlamadan
def validate_schema_completeness(model_class: type) -> list[str]:
    """Zorunlu alanların tanımlandığını kontrol eder."""
    issues = []
    
    for field_name, field_info in model_class.model_fields.items():
        if field_info.is_required() and field_info.annotation is None:
            issues.append(f"Tip annotation eksik: {field_name}")
    
    return issues
```

---

## References

- `pydantic-v2-model-definition-skill/SKILL.md` — model tanımı
- `migration-strategy-skill/SKILL.md` — DB migration
- `task-dependency-ordering-skill/SKILL.md` — görev sırası
