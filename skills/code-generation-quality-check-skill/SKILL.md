---
name: code-generation-quality-check
description: Coder AI için — LLM'den gelen kod çıktısını üretim öncesinde hızlıca kalite kontrolünden geçirmek; sık yapılan LLM hatalarını otomatik tespit etmek.
---

## Purpose

LLM bazen placeholder `pass` bırakır, gereksiz print ekler veya test kodu üretir.
Kalite kontrol bu sorunları diske yazmadan önce yakalar.
Kısa ve ucuz kontroller reviewer'dan önce devreye girer.

---

## When to Apply

- Worker LLM'den kod aldıktan sonra, diske yazmadan önce
- Validator node'unda basit pattern kontrolleri yapılırken
- LLM çıktısı şüpheli göründüğünde

---

## Rules

- `pass` ile biten fonksiyon: muhtemelen unimplemented → reddet.
- `TODO` / `FIXME` yorumları: LLM tamamlamamış → reddet.
- `print(` production kodunda: uyarı (opsiyonel).
- Dosya tamamen boş veya sadece import'lardan oluşuyor: reddet.
- Maksimum 100ms sürmeli — ağır analiz değil.

---

## Guidelines

```python
import re

class CodeQualityIssue:
    def __init__(self, severity: str, message: str):
        self.severity = severity  # "error" | "warning"
        self.message = message

def quick_quality_check(
    code: str,
    file_path: str,
) -> list[CodeQualityIssue]:
    issues = []
    lines = code.strip().splitlines()
    
    if not lines:
        issues.append(CodeQualityIssue("error", "Dosya boş"))
        return issues
    
    # Sadece import'lardan oluşuyor mu?
    non_import = [
        l for l in lines
        if l.strip() and not l.startswith(("import ", "from ", "#"))
    ]
    if not non_import:
        issues.append(CodeQualityIssue("error", "Sadece import satırları var, implementasyon yok"))
    
    # Unimplemented fonksiyon
    func_pass_pattern = re.compile(
        r'def \w+[^:]+:\s*\n\s+pass\s*$',
        re.MULTILINE
    )
    if func_pass_pattern.search(code):
        issues.append(CodeQualityIssue("error", "Boş fonksiyon(lar) var (pass)"))
    
    # TODO/FIXME
    if re.search(r'#\s*(TODO|FIXME|HACK|XXX)', code, re.IGNORECASE):
        issues.append(CodeQualityIssue("error", "TODO/FIXME yorumları var — implementasyon eksik"))
    
    # Print statements (warning)
    if "print(" in code and not file_path.endswith("test_"):
        issues.append(CodeQualityIssue("warning", "print() kullanımı — logger tercih edilmeli"))
    
    return issues

def has_blocking_issues(issues: list[CodeQualityIssue]) -> bool:
    return any(i.severity == "error" for i in issues)
```

---

## References

- `validator-node-implementation-skill/SKILL.md` — validator
- `worker-node-implementation-skill/SKILL.md` — worker
- `llm-output-parsing-skill/SKILL.md` — çıktı parse
