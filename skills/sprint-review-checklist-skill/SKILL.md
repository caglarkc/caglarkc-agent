---
name: sprint-review-checklist
description: Planner AI için — sprint tamamlanmadan önce gözden geçirilmesi gereken maddelerin kontrol listesi.
---

## Purpose

Sprint bitti ama gözden kaçan detaylar var.
Review checklist: tüm dosyalar yazıldı mı, testler geçti mi, dokümantasyon güncellendi mi?
Sistematik kontrol, eksik kalan işleri önler.

---

## When to Apply

- Reviewer node sprint çıktısını değerlendirirken
- Sprint tamamlandı bildirimi gönderilmeden önce
- Kullanıcıya sunum yapılmadan önce

---

## Rules

- Checklist: dosya tamamlama, test geçişi, linter, import kontrol.
- Başarısız madde: sprint `needs_review` durumuna geçer.
- Kritik madde başarısız: sprint tamamlanmış sayılmaz.
- Checklist sonucu state'e kaydedilir.

---

## Guidelines

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class CheckItem:
    name: str
    critical: bool
    check_fn: Callable[[dict], bool]

SPRINT_REVIEW_CHECKLIST: list[CheckItem] = [
    CheckItem(
        "Tüm dosyalar tamamlandı",
        critical=True,
        check_fn=lambda s: all(
            v == "done" for v in s.get("file_registry", {}).values()
        ),
    ),
    CheckItem(
        "Başarısız görev yok",
        critical=True,
        check_fn=lambda s: not any(
            t.get("status") == "failed" for t in s.get("tasks", [])
        ),
    ),
    CheckItem(
        "Linter hataları yok",
        critical=False,
        check_fn=lambda s: s.get("linter_passed", False),
    ),
    CheckItem(
        "Testler geçti",
        critical=False,
        check_fn=lambda s: s.get("tests_passed", True),
    ),
]

def run_review_checklist(
    state: dict,
    checklist: list[CheckItem] = SPRINT_REVIEW_CHECKLIST,
) -> dict:
    results = []
    all_critical_passed = True
    
    for item in checklist:
        passed = item.check_fn(state)
        results.append({
            "name":     item.name,
            "critical": item.critical,
            "passed":   passed,
        })
        if item.critical and not passed:
            all_critical_passed = False
    
    status = "completed" if all_critical_passed else "needs_review"
    return {
        "review_checklist": results,
        "sprint_status":    status,
    }

def format_checklist(results: list[dict]) -> str:
    lines = ["Sprint Review Checklist:"]
    for r in results:
        mark = "✓" if r["passed"] else ("✗" if r["critical"] else "⚠")
        lines.append(f"  {mark} {r['name']}")
    return "\n".join(lines)
```

---

## References

- `reviewer-node-implementation-skill/SKILL.md` — reviewer node
- `code-review-checklist-skill/SKILL.md` — kod inceleme listesi
- `sprint-completion-celebration-skill/SKILL.md` — tamamlanma bildirimi
