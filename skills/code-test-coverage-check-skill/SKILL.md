---
name: code-test-coverage-check
description: Coder AI için — üretilen Python kodunun test kapsamını ölçmek ve minimum eşiği karşılamayan modülleri raporlamak.
---

## Purpose

Kod yazıldı ama test yok — güven yok.
Coverage check: üretilen her modül için test kapsamı hesaplanır.
Minimum eşik altında kalan modüller: ek test yazılması için işaretlenir.

---

## When to Apply

- Validator node test geçişini doğrularken
- Sprint sonu kalite raporunda
- Reviewer "test eksik" uyarısı verdiğinde

---

## Rules

- Minimum coverage: %70 (konfigüre edilebilir).
- Araç: pytest-cov.
- Rapor: modül bazında satır kapsamı yüzdesi.
- Threshold altı: sprint `needs_review`'a geçer, hata değil.

---

## Guidelines

```python
import subprocess
import json

MIN_COVERAGE = 70.0

def run_coverage(
    test_path: str = "tests/",
    source_path: str = "src/",
    min_coverage: float = MIN_COVERAGE,
) -> dict:
    result = subprocess.run(
        [
            "python", "-m", "pytest",
            f"--cov={source_path}",
            "--cov-report=json",
            "--cov-report=term-missing",
            "-q", test_path,
        ],
        capture_output=True, text=True,
    )
    
    coverage_data = _parse_coverage_json(".coverage.json")
    summary = _summarize(coverage_data, min_coverage)
    summary["test_exit_code"] = result.returncode
    return summary

def _parse_coverage_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _summarize(data: dict, threshold: float) -> dict:
    files = data.get("files", {})
    below = []
    total_pct = 0.0
    
    for fpath, info in files.items():
        pct = info.get("summary", {}).get("percent_covered", 0)
        total_pct += pct
        if pct < threshold:
            below.append({"file": fpath, "coverage": round(pct, 1)})
    
    avg = total_pct / len(files) if files else 0
    return {
        "average_coverage": round(avg, 1),
        "below_threshold":  below,
        "passed":           avg >= threshold and not below,
        "file_count":       len(files),
    }

def format_coverage_report(summary: dict) -> str:
    lines = [f"Test Kapsamı: %{summary['average_coverage']}"]
    if summary["below_threshold"]:
        lines.append(f"\nEşik altı ({MIN_COVERAGE}%) modüller:")
        for item in summary["below_threshold"]:
            lines.append(f"  - {item['file']}: %{item['coverage']}")
    else:
        lines.append("Tüm modüller eşiği karşılıyor.")
    return "\n".join(lines)
```

---

## References

- `test-coverage-reporting-skill/SKILL.md` — test kapsam raporu
- `validator-node-implementation-skill/SKILL.md` — validator node
- `integration-test-setup-skill/SKILL.md` — entegrasyon test kurulumu
