---
name: code-security-scan
description: Coder AI için — üretilen kodda güvenlik açıklarını tespit etmek; SQL injection, hardcoded secret, path traversal gibi yaygın sorunları bulmak.
---

## Purpose

LLM güvenli olmayan kod üretebilir — örnek veriden kopyalanmış hardcoded secret.
Güvenlik taraması: üretilen her dosya teslim edilmeden önce kontrol edilir.
Otomatik tarama: bandit + regex tabanlı pattern matching.

---

## When to Apply

- Validator node dosyayı onaylamadan önce
- DB sorgusu veya HTTP isteği içeren kod üretildiğinde
- Harici input işleyen fonksiyon yazıldığında

---

## Rules

- Tarama araçları: bandit (otomatik), regex patterns (ek kontrol).
- Kritik bulgular: HIGH severity → kod reddedilir, retry.
- Orta bulgular: uyarı, planner kararına bırakılır.
- Hardcoded secret: API key pattern'ı regex ile bulunur.

---

## Guidelines

```python
import re
import subprocess

SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|token|secret|password)\s*=\s*["\'][^"\']{8,}["\']', "hardcoded secret"),
    (r'(?i)sk-[a-zA-Z0-9]{20,}',    "OpenAI API key"),
    (r'(?i)AIza[0-9A-Za-z_-]{35}',  "Google API key"),
]

SQL_INJECTION_PATTERNS = [
    (r'execute\s*\(\s*f["\']',       "f-string in SQL execute"),
    (r'execute\s*\(\s*"[^"]*%s',     "string format in SQL"),
]

def scan_for_secrets(code: str) -> list[dict]:
    findings = []
    for line_no, line in enumerate(code.splitlines(), 1):
        for pattern, name in SECRET_PATTERNS:
            if re.search(pattern, line):
                findings.append({
                    "line": line_no,
                    "type": name,
                    "severity": "high",
                    "snippet": line.strip()[:80],
                })
    return findings

def scan_sql_injection(code: str) -> list[dict]:
    findings = []
    for line_no, line in enumerate(code.splitlines(), 1):
        for pattern, name in SQL_INJECTION_PATTERNS:
            if re.search(pattern, line):
                findings.append({
                    "line": line_no,
                    "type": name,
                    "severity": "high",
                    "snippet": line.strip()[:80],
                })
    return findings

def run_bandit(file_path: str) -> list[dict]:
    result = subprocess.run(
        ["bandit", "-f", "json", "-q", file_path],
        capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):
        return []
    import json
    try:
        data = json.loads(result.stdout)
        return data.get("results", [])
    except json.JSONDecodeError:
        return []

def full_security_scan(code: str, file_path: str) -> dict:
    findings = scan_for_secrets(code) + scan_sql_injection(code)
    bandit   = run_bandit(file_path)
    high     = [f for f in findings if f.get("severity") == "high"]
    return {
        "passed":    len(high) == 0,
        "high":      len(high),
        "findings":  findings,
        "bandit":    bandit,
    }
```

---

## References

- `validator-node-implementation-skill/SKILL.md` — validator node
- `code-review-checklist-skill/SKILL.md` — kod inceleme listesi
- `input-validation-patterns-skill/SKILL.md` — giriş doğrulama
