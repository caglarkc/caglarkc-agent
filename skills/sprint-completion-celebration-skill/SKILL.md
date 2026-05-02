---
name: sprint-completion-celebration
description: Planner AI için — sprint başarıyla tamamlandığında kullanıcıya özet sunan ve sonraki adımı soran kapanış mesajı yazmak.
---

## Purpose

Sprint bitti ama kullanıcı habersizse motivasyon düşer.
Tamamlanma mesajı ne yapıldığını özetler ve sonraki sprint'e köprü kurar.
Kısa ve bilgilendirici — uzun kutlama metinleri değil.

---

## When to Apply

- Sprint durumu `done` olduğunda
- Reviewer node onayladıktan sonra
- PM mode `[SOHBET]`'e dönerken

---

## Rules

- Tamamlanan dosya listesi gösterilir.
- Karar (ADR, onay) referansı verilmez — sadece sonuç.
- Sonraki sprint sorusu açık uçlu.
- Hata olmadan bitmişse: "Başarıyla tamamlandı".
- Bazı dosyalar başarısız olduysa: "X dosya tamamlandı, Y başarısız" .

---

## Guidelines

```python
async def generate_completion_message(
    state: OrchestratorState
) -> str:
    file_registry = state.get("file_registry", {})
    done_files = [p for p, s in file_registry.items() if s == "done"]
    failed_files = [p for p, s in file_registry.items() if s == "failed"]
    sprint_id = state.get("sprint_id", "?")
    
    if failed_files:
        status_line = (
            f"{len(done_files)} dosya tamamlandı, "
            f"{len(failed_files)} dosya başarısız"
        )
    else:
        status_line = f"{len(done_files)} dosya başarıyla yazıldı"
    
    files_list = "\n".join(f"  ✓ {f}" for f in done_files)
    
    return (
        f"Sprint {sprint_id} tamamlandı!\n\n"
        f"Durum: {status_line}\n\n"
        f"Yazılan dosyalar:\n{files_list}\n\n"
        f"Sırada ne yapalım?"
    )
```

PM formatı:
```
[SOHBET] Sprint 3 tamamlandı!

Durum: 8 dosya başarıyla yazıldı

Yazılan dosyalar:
  ✓ src/graph/nodes/planner.py
  ✓ src/graph/nodes/dispatcher.py
  ✓ tests/test_planner.py
  ...

Sırada ne yapalım?
```

---

## References

- `sprint-summary-generation-skill/SKILL.md` — sprint özeti
- `progress-report-generation-skill/SKILL.md` — ilerleme raporu
- `pm-mode-skill/SKILL.md` — PM modları
