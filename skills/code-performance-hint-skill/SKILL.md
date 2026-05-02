---
name: code-performance-hint
description: Coder AI için — üretilen kodda belirgin performans sorunlarını tespit edip iyileştirme önerileri sunmak.
---

## Purpose

Doğru çalışan kod yeterince hızlı olmayabilir.
Performans ipuçları: N+1 sorgu, gereksiz kopya, senkron blok gibi yaygın sorunları işaret eder.
LLM ürettiği kodu ikinci gözle inceler; kritik yolu tespit eder.

---

## When to Apply

- Reviewer node büyük veri işleyen kod incelediğinde
- DB sorgusu döngü içindeyse (N+1 riski)
- Büyük liste/dict kopyalamaları görüldüğünde

---

## Rules

- Sadece belirgin sorunlar raporlanır — micro-optimizasyon değil.
- Her öneri: sorunu açıkla + somut alternatif göster.
- Max 3 öneri (odak koru).
- Öneri uygulaması: zorunlu değil, planner kararı.

---

## Guidelines

```python
import ast
import re

PERFORMANCE_PATTERNS = [
    (
        r'for\s+\w+\s+in\s+\w+.*:\s*\n.*\.query\(',
        "Döngü içi DB sorgusu (N+1 riski)",
        "Sorguyu döngü dışına çıkar veya bulk fetch kullan",
    ),
    (
        r'list\(dict\.items\(\)\)',
        "Gereksiz list() dönüşümü",
        "dict.items() doğrudan iterable — list() sarma gereksiz",
    ),
    (
        r'time\.sleep\(',
        "Senkron sleep (async blok)",
        "asyncio.sleep() kullan",
    ),
]

def scan_performance_issues(code: str) -> list[dict]:
    issues = []
    for line_no, line in enumerate(code.splitlines(), 1):
        for pattern, problem, suggestion in PERFORMANCE_PATTERNS:
            if re.search(pattern, line):
                issues.append({
                    "line":       line_no,
                    "problem":    problem,
                    "suggestion": suggestion,
                    "snippet":    line.strip()[:80],
                })
    return issues[:3]

def analyze_complexity(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}
    
    nested_loops = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if child is not node and isinstance(child, (ast.For, ast.While)):
                    nested_loops += 1
    
    return {"nested_loops": nested_loops, "likely_o_n2": nested_loops > 0}

def format_performance_hints(issues: list[dict], complexity: dict) -> str:
    if not issues and not complexity.get("likely_o_n2"):
        return "Belirgin performans sorunu yok."
    lines = ["Performans ipuçları:"]
    for i in issues:
        lines.append(f"  Satır {i['line']}: {i['problem']}")
        lines.append(f"    Öneri: {i['suggestion']}")
    if complexity.get("likely_o_n2"):
        lines.append("  İç içe döngü: O(n²) karmaşıklık riski.")
    return "\n".join(lines)
```

---

## References

- `code-refactor-suggestion-skill/SKILL.md` — refactor önerileri
- `reviewer-node-implementation-skill/SKILL.md` — reviewer node
- `code-review-checklist-skill/SKILL.md` — kod inceleme listesi
