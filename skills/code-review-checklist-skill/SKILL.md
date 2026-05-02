---
name: code-review-checklist
description: Planner AI için — reviewer node'unun üretilen kodu değerlendirirken kullandığı kontrol listesini uygulamak; geçme/kalma kararı vermek.
---

## Purpose

Reviewer node keyfi karar vermez — tanımlı kriterlere göre değerlendirir.
Checklist hem hız hem tutarlılık sağlar.
Her madde "geçti / başarısız / atlandı" olarak işaretlenir.

---

## When to Apply

- Reviewer node kodu değerlendirirken
- Sprint tamamlanma öncesi son kontrol yapılırken
- Kod kalitesi sorgulandığında

---

## Rules

- Tüm kritik maddeler geçmeden sprint `done` yapılamaz.
- Opsiyonel maddeler başarısız olursa sadece not düşülür.
- Reviewer 3 defadan fazla aynı hatayı bulamazsa devam edilir (sonsuz döngü önleme).
- Değerlendirme sonucu Decision olarak kaydedilir.

---

## Guidelines

```python
from dataclasses import dataclass
from enum import Enum

class CheckResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"

@dataclass
class CheckItem:
    id: str
    description: str
    critical: bool
    result: CheckResult = CheckResult.SKIP

REVIEW_CHECKLIST = [
    CheckItem("syntax",    "Syntax hatası yok",               critical=True),
    CheckItem("imports",   "Import'lar doğru ve tam",         critical=True),
    CheckItem("types",     "Type hint'ler mevcut",            critical=False),
    CheckItem("async",     "Async/await doğru kullanılmış",   critical=True),
    CheckItem("error",     "Hata yönetimi var",               critical=True),
    CheckItem("tests",     "Test dosyası yazılmış",           critical=False),
    CheckItem("no_secret", "Gizli anahtar hard-code yok",     critical=True),
    CheckItem("log",       "Kritik adımlar loglanıyor",       critical=False),
]

def evaluate_checklist(
    items: list[CheckItem]
) -> tuple[bool, list[str]]:
    failures = [
        item.description
        for item in items
        if item.critical and item.result == CheckResult.FAIL
    ]
    return len(failures) == 0, failures
```

PM review formatı:
```
[REVIEW] Kod inceleme sonucu:

✓ Syntax hatası yok
✓ Import'lar doğru
✓ Async/await doğru
✗ Hata yönetimi eksik — worker node try/except yok
✓ Gizli anahtar yok

Sonuç: BAŞARISIZ
Düzeltilmesi gereken: Hata yönetimi
```

---

## References

- `sprint-completion-validation-skill/SKILL.md` — tamamlanma
- `review-cycle-limit-enforcement-skill/SKILL.md` — döngü limiti
- `test-strategy-planning-skill/SKILL.md` — test planı
