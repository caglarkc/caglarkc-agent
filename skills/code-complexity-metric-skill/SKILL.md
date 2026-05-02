---
name: code-complexity-metric
description: Coder AI için — üretilen kodun siklomatik karmaşıklığını ve satır sayısını ölçmek; çok karmaşık fonksiyonları işaretlemek.
---

## Purpose

LLM bazen tek devasa fonksiyon üretir — test edilmesi ve bakımı zor.
Karmaşıklık metriği: siklomatik sayı + satır sayısı ile basit ölçüm.
Aşan fonksiyon: parçalara bölünmesi için reviewer'a raporlanır.

---

## When to Apply

- Validator node kod kalitesini değerlendirirken
- Reviewer "çok karmaşık" kararı vermeden önce
- Sprint sonunda teknik borç analizi yapılırken

---

## Rules

- Siklomatik limit: 10 (McCabe).
- Fonksiyon uzunluğu: maks 50 satır.
- Sınıf boyutu: maks 200 satır.
- Aşan: uyarı (hata değil), yeniden yazma önerisi.

---

## Guidelines

```python
import ast

MAX_CYCLOMATIC = 10
MAX_FUNC_LINES = 50
MAX_CLASS_LINES = 200

def cyclomatic_complexity(fn_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    complexity = 1
    for node in ast.walk(fn_node):
        if isinstance(node, (ast.If, ast.While, ast.For,
                              ast.ExceptHandler, ast.With,
                              ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity

def analyze_code_complexity(code: str) -> list[dict]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    issues = []
    lines  = code.splitlines()
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cc       = cyclomatic_complexity(node)
            fn_lines = (node.end_lineno or node.lineno) - node.lineno + 1
            
            if cc > MAX_CYCLOMATIC:
                issues.append({
                    "type":    "high_complexity",
                    "name":    node.name,
                    "line":    node.lineno,
                    "value":   cc,
                    "limit":   MAX_CYCLOMATIC,
                    "message": f"Siklomatik karmaşıklık {cc} (limit {MAX_CYCLOMATIC})",
                })
            if fn_lines > MAX_FUNC_LINES:
                issues.append({
                    "type":    "long_function",
                    "name":    node.name,
                    "line":    node.lineno,
                    "value":   fn_lines,
                    "limit":   MAX_FUNC_LINES,
                    "message": f"Fonksiyon {fn_lines} satır (limit {MAX_FUNC_LINES})",
                })
    
    return issues

def format_complexity_report(issues: list[dict]) -> str:
    if not issues:
        return "Karmaşıklık limitleri aşılmadı."
    lines = ["Karmaşıklık uyarıları:"]
    for i in issues:
        lines.append(f"  {i['name']} (satır {i['line']}): {i['message']}")
    return "\n".join(lines)
```

---

## References

- `code-refactor-suggestion-skill/SKILL.md` — refactor önerileri
- `code-review-checklist-skill/SKILL.md` — kod inceleme
- `technical-debt-logging-skill/SKILL.md` — teknik borç kaydı
