---
name: code-module-boundary
description: Coder AI için — modüller arası sınırları net çizmek; hangi fonksiyonların public, hangilerinin internal olduğunu tanımlamak.
---

## Purpose

Her şey herkese açık olunca kapsülleme bozulur.
Modül sınırı: public API — `__init__.py` üzerinden açılır; internal — `_` ile gizlenir.
Dışarıdan sadece gerekli arayüz görünür.

---

## When to Apply

- Yeni paket veya modül oluşturulurken
- `__init__.py` içeriği tanımlanırken
- Refactor sırasında sızdıran soyutlama düzeltilirken

---

## Rules

- Public: `__init__.py`'de `__all__` listesinde.
- Internal: `_` öneki (tek alt çizgi).
- Gizli: `__` çift alt çizgi (sınıf içi).
- Modüller arası: bağımlılık tek yönlü.

---

## Guidelines

```python
# src/sprint/__init__.py — public API tanımı
from .planner import SprintPlanner
from .executor import SprintExecutor
from .models import SprintState, Task

__all__ = [
    "SprintPlanner",
    "SprintExecutor",
    "SprintState",
    "Task",
]

# src/sprint/planner.py — internal yardımcı gizli
class SprintPlanner:
    def create_plan(self, goal: str) -> dict:    # public
        tasks = self._decompose(goal)
        return {"tasks": tasks}

    def _decompose(self, goal: str) -> list:     # internal
        pass

    def __validate_internal(self) -> bool:      # gizli
        pass

# Modül bağımlılık sırası (döngüsel bağımlılık yok)
# models → utils → planner → executor → orchestrator
# Kural: üst katman alt katmanı import eder, tersi olmaz.

def check_circular_imports(module_deps: dict[str, list[str]]) -> list[tuple[str, str]]:
    cycles = []
    visited: set[str] = set()

    def dfs(node: str, path: list[str]) -> None:
        if node in path:
            cycle_start = path.index(node)
            cycles.append((path[cycle_start], node))
            return
        if node in visited:
            return
        visited.add(node)
        for dep in module_deps.get(node, []):
            dfs(dep, path + [node])

    for m in module_deps:
        dfs(m, [])
    return cycles
```

---

## References

- `code-class-design-skill/SKILL.md` — sınıf tasarımı
- `dependency-injection-patterns-skill/SKILL.md` — bağımlılık enjeksiyonu
- `abstract-base-class-skill/SKILL.md` — soyut temel sınıf
