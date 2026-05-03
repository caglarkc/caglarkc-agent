---
name: subprocess-async
description: Coder AI için — asyncio.create_subprocess_exec veya asyncio.create_subprocess_shell ile harici komutları async olarak çalıştırmak.
---

## Purpose

`subprocess.run()` event loop'u bloklar — async kodda kullanılamaz.
`asyncio.create_subprocess_exec` komutları non-blocking çalıştırır.
Harici araç (git, ruff, pytest) çağrısı için gerekli.

---

## When to Apply

- Git komutu çalıştırılırken (status, diff, commit)
- Linter veya formatter çağrılırken (ruff, black)
- Test komutu çalıştırılırken (pytest)
- Harici CLI aracı entegre edilirken

---

## Rules

- `create_subprocess_shell` yerine `create_subprocess_exec` tercih edilir (injection güvenliği).
- Timeout ayarlanır: uzun süren komutlar sonlandırılır.
- Çıkış kodu 0 değilse `SubprocessError` fırlatılır.
- stdout ve stderr ayrı ayrı yakalanır.
- Kullanıcı girdisi argümana doğrudan geçirilmez — validate edilir.

---

## Guidelines

```python
import asyncio
from typing import tuple as Tuple

class SubprocessError(Exception):
    def __init__(self, cmd: list, returncode: int, stderr: str):
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Komut başarısız ({returncode}): {' '.join(cmd)}\n{stderr}")

async def run_command(
    args: list[str],
    cwd: str | None = None,
    timeout: float = 60.0
) -> tuple[str, str]:
    """
    Returns: (stdout, stderr)
    Raises: SubprocessError, asyncio.TimeoutError
    """
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise
    
    stdout = stdout_b.decode("utf-8", errors="replace").strip()
    stderr = stderr_b.decode("utf-8", errors="replace").strip()
    
    if proc.returncode != 0:
        raise SubprocessError(args, proc.returncode, stderr)
    
    return stdout, stderr
```

Kullanım örnekleri:
```python
# Ruff kontrol
stdout, _ = await run_command(["ruff", "check", "src/"])

# Git durumu
stdout, _ = await run_command(["git", "status", "--porcelain"])

# Pytest
stdout, stderr = await run_command(
    ["pytest", "tests/", "-v", "--tb=short"],
    timeout=120.0
)
```

---

## References

- `graceful-shutdown-implementation-skill/SKILL.md` — process yönetimi
- `async-function-template-skill/SKILL.md` — async pattern
- `logging-patterns-skill/SKILL.md` — çıktı loglama
