---
name: cascading-failure-prevention
description: Planner AI için — bir worker veya dosyanın başarısız olmasının zincirleme olarak bağımlı görevleri de çökertmesini önlemek; izole hata yönetimi.
---

## Purpose

Tek bir hata tüm sprint'i çökertmez.
Bağımsız dosyalar başarısız bir dosyadan etkilenmez.
Bağımlı dosyalar başarısız bağımlılık tespit edilince beklemeye alınır, iptal edilmez.

---

## When to Apply

- Worker başarısız olduğunda dispatcher yeniden atama yaparken
- Reviewer bağımlılık analizi yaparken
- Sprint failed kararı verilmeden önce

---

## Rules

- Başarısız dosya yalnızca ona bağımlı dosyaları etkiler.
- Bağımsız dosyalar paralel çalışmaya devam eder.
- Bağımlı dosya: failed bağımlılık varsa `blocked` statüsüne alınır.
- `blocked` dosya otomatik `failed` sayılmaz — bağımlılık düzelinceye kadar bekler.
- Sprint failed: yalnızca kritik yolda başarısız dosya varsa.

---

## Guidelines

Bağımlılık etkisi analizi:
```
Sprint dosyaları:
A: state.py ← bağımsız
B: planner.py ← A'ya bağımlı
C: dispatcher.py ← A'ya bağımlı (B'ye değil)
D: test_planner.py ← B'ye bağımlı

A başarısız olursa:
→ B: blocked (A bağımlılığı çözülmedi)
→ C: blocked (A bağımlılığı çözülmedi)
→ D: blocked (B blocked olduğu için)

A başarısız ama retry ile düzelirse:
→ B, C, D: planned'a geri alınır, devam eder
```

Reviewer izole karar:
```python
def analyze_sprint_health(state: OrchestratorState) -> SprintHealthReport:
    file_registry = state.get("file_registry", {})
    dependencies = state.get("dependencies", {})
    
    failed_files = {f for f, s in file_registry.items() if s == "failed"}
    blocked_files = set()
    healthy_files = set()
    
    for file_path, deps in dependencies.items():
        if any(d in failed_files for d in deps):
            blocked_files.add(file_path)
        elif file_registry.get(file_path) == "done":
            healthy_files.add(file_path)
    
    # Kritik yol analizi
    is_critical_failure = any(
        f in failed_files
        for f in get_critical_path_files(dependencies)
    )
    
    return SprintHealthReport(
        failed=failed_files,
        blocked=blocked_files,
        healthy=healthy_files,
        critical_failure=is_critical_failure
    )
```

---

## References

- `file-dependency-graph-design-skill/SKILL.md` — bağımlılık
- `worker-failure-triage-skill/SKILL.md` — hata analizi
- `review-cycle-limit-enforcement-skill/SKILL.md` — döngü limiti
