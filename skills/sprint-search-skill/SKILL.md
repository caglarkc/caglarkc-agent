---
name: sprint-search
description: Planner AI için — geçmiş sprint kayıtlarında tam metin arama yapmak; benzer görevleri veya eski kararları bulmak.
---

## Purpose

"Bunu daha önce yapmış mıydık?" sorusu yanıtsız kalır.
Sprint geçmişinde arama, tekrar eden çalışmayı önler ve eski çözümleri geri getirir.
SQLite FTS5 ile hızlı tam metin arama sağlanır.

---

## When to Apply

- Kullanıcı "daha önce X yapmış mıydık?" diye sorduğunda
- Planner benzer görev planlarken geçmişe başvurmak istediğinde
- Sprint retrospective'inde önceki kararlar araştırılırken

---

## Rules

- Arama: sprint_id, goal, task descriptions, dosya isimleri üzerinde.
- FTS5 yoksa LIKE sorgusu fallback.
- Sonuçlar: en son sprint önce, max 10 sonuç.
- Bulunan sprint: özet bilgi döndürülür (id, tarih, goal, sonuç).

---

## Guidelines

```python
import sqlite3
from dataclasses import dataclass

@dataclass
class SprintSearchResult:
    sprint_id: str
    goal: str
    created_at: str
    status: str
    relevance_snippet: str

def search_sprints(
    db_path: str,
    query: str,
    max_results: int = 10,
) -> list[SprintSearchResult]:
    conn = sqlite3.connect(db_path)
    try:
        # FTS5 denemesi
        results = _fts_search(conn, query, max_results)
        if results is None:
            results = _like_search(conn, query, max_results)
        return results
    finally:
        conn.close()

def _fts_search(conn, query, max_results):
    try:
        rows = conn.execute(
            """
            SELECT sprint_id, goal, created_at, status,
                   snippet(sprints_fts, 1, '<b>', '</b>', '...', 20)
            FROM sprints_fts
            WHERE sprints_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, max_results),
        ).fetchall()
        return [SprintSearchResult(*r) for r in rows]
    except sqlite3.OperationalError:
        return None

def _like_search(conn, query, max_results):
    pattern = f"%{query}%"
    rows = conn.execute(
        """
        SELECT sprint_id, goal, created_at, status, goal
        FROM sprints
        WHERE goal LIKE ? OR sprint_id LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (pattern, pattern, max_results),
    ).fetchall()
    return [SprintSearchResult(*r) for r in rows]

def format_search_results(results: list[SprintSearchResult]) -> str:
    if not results:
        return "Eşleşen sprint bulunamadı."
    lines = [f"Bulunan {len(results)} sprint:"]
    for r in results:
        lines.append(f"  [{r.sprint_id}] {r.created_at[:10]} — {r.goal[:60]}")
    return "\n".join(lines)
```

---

## References

- `sprint-history-query-skill/SKILL.md` — geçmiş sprint sorgusu
- `sprint-export-skill/SKILL.md` — sprint dışa aktarma
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
