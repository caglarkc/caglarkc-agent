---
name: sprint-acceptance-testing
description: Planner AI için — sprint sonu kabul testlerini tanımlamak ve çalıştırmak; kullanıcı hikayelerinin gerçeklendiğini doğrulamak.
---

## Purpose

Kod yazıldı ama kullanıcı beklentisini karşılıyor mu?
Kabul testleri: "bunu yapabilmeli" maddelerini otomatik kontrol eder.
Reviewer node'dan ayrı — iş değeri perspektifinden bakılır.

---

## When to Apply

- Sprint tamamlandığında kullanıcıya teslimden önce
- Kabul kriterleri tanımlanmış user story'ler varken
- "Bu özellik çalışıyor mu?" sorusu yanıtlanırken

---

## Rules

- Her kabul kriteri: evet/hayır sonuçlu test.
- Test yöntemi: import + çağır, CLI komut, veya LLM değerlendirme.
- Başarısız kriter: sprint `accepted_with_notes` olur.
- Raporlama: kullanıcıya sade dilde.

---

## Guidelines

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class AcceptanceTest:
    criterion: str
    test_fn:   Callable[[], bool]
    story_id:  str

def run_acceptance_tests(
    tests: list[AcceptanceTest],
) -> dict:
    results = []
    passed  = 0
    failed  = 0
    
    for test in tests:
        try:
            ok = test.test_fn()
        except Exception as exc:
            ok = False
        
        results.append({
            "criterion": test.criterion,
            "story_id":  test.story_id,
            "passed":    ok,
        })
        if ok:
            passed += 1
        else:
            failed += 1
    
    return {
        "results": results,
        "passed":  passed,
        "failed":  failed,
        "status":  "accepted" if failed == 0 else "accepted_with_notes",
    }

def format_acceptance_report(result: dict) -> str:
    lines = [
        f"Kabul Testi: {result['passed']}/{result['passed']+result['failed']} geçti",
        "",
    ]
    for r in result["results"]:
        mark = "✓" if r["passed"] else "✗"
        lines.append(f"  {mark} {r['criterion']}")
    
    if result["failed"]:
        lines.append(f"\nNot: {result['failed']} kriter karşılanmadı.")
    
    return "\n".join(lines)

# Örnek test tanımları
def make_file_exists_test(file_path: str, story_id: str) -> AcceptanceTest:
    from pathlib import Path
    return AcceptanceTest(
        criterion=f"{file_path} dosyası oluşturuldu",
        test_fn=lambda: Path(file_path).exists(),
        story_id=story_id,
    )
```

---

## References

- `sprint-review-checklist-skill/SKILL.md` — review kontrol listesi
- `sprint-user-story-mapping-skill/SKILL.md` — kullanıcı hikayesi
- `integration-test-setup-skill/SKILL.md` — entegrasyon test
