---
name: sprint-quick-win
description: Planner AI için — sprint planında 5-10 dakikada tamamlanabilecek kolay görevleri önce sıralamak; hızlı momentum kazanmak.
---

## Purpose

Uzun görevlerle başlamak morali bozar.
Quick win: küçük, hızlı görevler önce yapılır — erken başarı hissi verir.
Sonraki büyük görevlere motivasyonla girilir.

---

## When to Apply

- Sprint planı sıralanırken
- İlk sprint veya yeni projeye başlanırken
- Kullanıcı "kolay başlayalım" dediğinde

---

## Rules

- Quick win: ≤10 dakika tahmini süre.
- Sıra: quick win'ler listenin başına alınır.
- Sayı: maks 3 quick win (fazlası gerçek ilerlemeyi geciktirir).
- Kullanıcıya bildir: "3 kolay görev ile başlıyoruz."

---

## Guidelines

```python
QUICK_WIN_THRESHOLD = 10  # dakika

def identify_quick_wins(
    tasks: list[dict],
    max_count: int = 3,
) -> tuple[list[dict], list[dict]]:
    quick = [
        t for t in tasks
        if t.get("estimated_minutes", 20) <= QUICK_WIN_THRESHOLD
        and t.get("status") == "planned"
        and not t.get("depends_on")  # Bağımlılığı olmayanlar
    ][:max_count]

    quick_ids = {t["id"] for t in quick}
    rest = [t for t in tasks if t["id"] not in quick_ids]
    return quick, rest

def reorder_with_quick_wins(tasks: list[dict]) -> list[dict]:
    quick, rest = identify_quick_wins(tasks)
    return quick + rest

def format_quick_win_message(quick_wins: list[dict]) -> str:
    if not quick_wins:
        return ""
    lines = [f"⚡ {len(quick_wins)} hızlı görev ile başlıyoruz:"]
    for q in quick_wins:
        lines.append(f"  • {q.get('description', q['id'])[:60]} (~{q.get('estimated_minutes', 5)} dk)")
    return "\n".join(lines)
```

---

## References

- `sprint-priority-matrix-skill/SKILL.md` — öncelik matrisi
- `sprint-capacity-planning-skill/SKILL.md` — kapasite planlaması
- `sprint-constraint-solver-skill/SKILL.md` — kısıt çözücü
