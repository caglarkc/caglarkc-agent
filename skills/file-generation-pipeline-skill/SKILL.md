---
name: file-generation-pipeline
description: Coder AI için — tek dosya üretimini aşamalı pipeline'a dönüştürmek; oluştur → doğrula → düzelt → kaydet.
---

## Purpose

Tek adımda dosya üretmek hataları gizler.
Pipeline: her aşama bağımsız kontrol edilebilir.
Başarısız aşama geri döner ve retry edilir — tüm süreç değil.

---

## When to Apply

- Worker node dosya üretirken
- Kod kalitesi garantisi gerektiren üretim süreçlerinde
- Multi-step validation iş akışında

---

## Rules

- Aşamalar: generate → lint → validate → write.
- Her aşama başarısız olabilir ve retry edilebilir.
- Maks retry: aşama başına 2.
- Son aşama (write) atomik — kısmi yazma yok.

---

## Guidelines

```python
from dataclasses import dataclass
from typing import Callable, Awaitable

@dataclass
class PipelineStage:
    name: str
    fn:   Callable[[str, dict], Awaitable[tuple[str, bool, str]]]
    # fn returns: (output, success, error_msg)

async def run_file_pipeline(
    task: dict,
    stages: list[PipelineStage],
    max_stage_retries: int = 2,
) -> tuple[str | None, list[str]]:
    content = ""
    errors  = []
    
    for stage in stages:
        success = False
        for attempt in range(max_stage_retries + 1):
            content, success, err = await stage.fn(content, task)
            if success:
                break
            errors.append(f"[{stage.name}] attempt {attempt+1}: {err}")
        
        if not success:
            return None, errors
    
    return content, errors

# Aşama tanımları
async def generate_stage(prev: str, task: dict) -> tuple[str, bool, str]:
    code = await generate_code_with_llm(task)
    return code, bool(code), "LLM boş yanıt verdi"

async def lint_stage(code: str, task: dict) -> tuple[str, bool, str]:
    from subprocess import run
    result = run(["ruff", "check", "--fix", "-"], input=code, capture_output=True, text=True)
    fixed  = result.stdout or code
    return fixed, result.returncode == 0, result.stderr

async def write_stage(code: str, task: dict) -> tuple[str, bool, str]:
    from pathlib import Path
    path = Path(task["file_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")
    return code, True, ""

DEFAULT_PIPELINE = [
    PipelineStage("generate", generate_stage),
    PipelineStage("lint",     lint_stage),
    PipelineStage("write",    write_stage),
]
```

---

## References

- `worker-node-implementation-skill/SKILL.md` — worker node
- `file-write-atomicity-skill/SKILL.md` — atomik yazma
- `linter-integration-skill/SKILL.md` — linter entegrasyonu
