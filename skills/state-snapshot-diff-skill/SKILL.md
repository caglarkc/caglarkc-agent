---
name: state-snapshot-diff
description: Coder AI için — iki LangGraph state snapshot arasındaki farkı göstermek; hangi alanların değiştiğini takip etmek.
---

## Purpose

Sprint boyunca state nasıl değişti? Hangi dosyalar tamamlandı?
Snapshot diff, iki state arasındaki değişimi gösterir.
Debug, audit ve recovery için kullanışlı.

---

## When to Apply

- Sprint sonrası state değişimi raporlanırken
- Hata ayıklama sırasında beklenmedik state değişimi araştırılırken
- Recovery öncesinde önceki vs. şimdiki state karşılaştırılırken

---

## Rules

- Sadece değişen alanlar gösterilir — aynı alanlar atlanır.
- Dict farkı: eklenen, silinen, değişen anahtarlar ayrı listelenir.
- Liste farkı: eklenen ve silinen öğeler gösterilir.
- Büyük state: sadece özet diff (tam diff değil).

---

## Guidelines

```python
from typing import Any

def diff_states(
    before: dict[str, Any],
    after: dict[str, Any],
    ignore_keys: set[str] | None = None,
) -> dict[str, Any]:
    ignore = ignore_keys or {"messages"}  # Büyük alanları atla
    changes = {}
    
    all_keys = set(before) | set(after)
    
    for key in all_keys:
        if key in ignore:
            continue
        
        before_val = before.get(key)
        after_val = after.get(key)
        
        if before_val == after_val:
            continue
        
        if isinstance(before_val, dict) and isinstance(after_val, dict):
            added = {k: v for k, v in after_val.items() if k not in before_val}
            removed = {k for k in before_val if k not in after_val}
            changed = {
                k: {"from": before_val[k], "to": after_val[k]}
                for k in before_val
                if k in after_val and before_val[k] != after_val[k]
            }
            if added or removed or changed:
                changes[key] = {"added": added, "removed": list(removed), "changed": changed}
        
        elif isinstance(before_val, list) and isinstance(after_val, list):
            before_set = set(str(x) for x in before_val)
            after_set = set(str(x) for x in after_val)
            changes[key] = {
                "added_count": len(after_set - before_set),
                "removed_count": len(before_set - after_set),
                "total": len(after_val),
            }
        
        else:
            changes[key] = {"from": before_val, "to": after_val}
    
    return changes

def format_state_diff(diff: dict) -> str:
    if not diff:
        return "State değişmedi."
    lines = ["State değişiklikleri:"]
    for key, change in diff.items():
        lines.append(f"  {key}: {change}")
    return "\n".join(lines)
```

---

## References

- `graph-state-inspection-skill/SKILL.md` — state okuma
- `checkpoint-inspection-skill/SKILL.md` — checkpoint
- `partial-sprint-recovery-skill/SKILL.md` — recovery
