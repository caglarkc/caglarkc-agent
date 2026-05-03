---
name: dead-letter-queue
description: Coder AI için — maksimum retry sayısını aşan ve işlenemeyen görevleri dead-letter queue'ya alarak raporlamak; sonsuz retry döngüsünü önlemek.
---

## Purpose

Bazı görevler hiçbir zaman başarıya ulaşamaz — sonsuz retry sistem kaynağını tüketir.
Dead-letter queue başarısız görevleri izole eder ve analiz için saklar.
Kullanıcı "neden başarısız?" diye sorduğunda DLQ raporlanır.

---

## When to Apply

- Worker max_retries aşıldığında
- `failed` durumuna geçen dosya yeniden planlanmayacaksa
- Sprint sonunda başarısız görevler raporlanırken

---

## Rules

- Max retry aşıldıktan sonra: `dead_letter` alanına eklenir.
- DLQ: `state["dead_letter_queue"]` — list of dicts.
- DLQ girdisi: file_path, reason, attempts, last_error.
- DLQ boyutu sınırsız değil — son 100 girdi saklanır.
- Sprint sonunda DLQ raporu kullanıcıya sunulur.

---

## Guidelines

```python
from dataclasses import dataclass, field, asdict

@dataclass
class DeadLetterEntry:
    file_path: str
    task_id: str
    attempts: int
    last_error: str
    failed_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

def add_to_dead_letter_queue(
    state: OrchestratorState,
    file_path: str,
    task_id: str,
    attempts: int,
    error: str,
) -> list[dict]:
    dlq = list(state.get("dead_letter_queue", []))
    
    entry = DeadLetterEntry(
        file_path=file_path,
        task_id=task_id,
        attempts=attempts,
        last_error=str(error)[:500],  # log sınırı
    )
    dlq.append(asdict(entry))
    
    # Max 100 girdi
    return dlq[-100:]

def format_dlq_report(dlq: list[dict]) -> str:
    if not dlq:
        return ""
    
    lines = [f"Başarısız görevler ({len(dlq)}):"]
    for entry in dlq:
        lines.append(
            f"  - {entry['file_path']} "
            f"({entry['attempts']} deneme): {entry['last_error'][:80]}"
        )
    return "\n".join(lines)
```

Worker'da kullanım:
```python
decision = decide_retry(error, attempt)
if decision == RetryDecision.FAIL_PERMANENT:
    updated_dlq = add_to_dead_letter_queue(
        state, file_path, task_id, attempt, str(error)
    )
    return {"dead_letter_queue": updated_dlq, "file_registry": ...}
```

---

## References

- `retry-decision-logic-skill/SKILL.md` — retry kararı
- `worker-failure-triage-skill/SKILL.md` — hata triage
- `progress-report-generation-skill/SKILL.md` — rapor
