---
name: dependency-graph-visualization
description: Planner AI için — proje modülleri arasındaki import bağımlılıklarını görsel grafik olarak göstermek; mimari kararları desteklemek.
---

## Purpose

"Hangi modül neye bağımlı?" sorusu görsel grafik olmadan zor cevaplanır.
Import bağımlılık grafiği circular dependency ve yüksek coupling'i ortaya çıkarır.
Mimari refactor kararlarında veri sunar.

---

## When to Apply

- Mimari review sırasında bağımlılıklar analiz edilirken
- Circular import sorunu araştırılırken
- Kullanıcı "modül yapısı nasıl?" diye sorduğunda

---

## Rules

- Analiz: `ast` ile static, runtime değil.
- Sadece iç modüller (`src/`) gösterilir.
- Circular dependency tespit edilirse uyarı üretilir.
- Çıktı: ASCII veya DOT format.

---

## Guidelines

```python
import ast
from pathlib import Path
from collections import defaultdict

def build_dependency_graph(src_dir: str = "src") -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    
    for py_file in Path(src_dir).rglob("*.py"):
        module = str(py_file).replace("/", ".").removesuffix(".py")
        
        try:
            with open(py_file) as f:
                tree = ast.parse(f.read())
        except (OSError, SyntaxError):
            continue
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("src."):
                    graph[module].append(node.module)
    
    return dict(graph)

def find_circular_deps(graph: dict[str, list[str]]) -> list[list[str]]:
    cycles = []
    visited = set()
    
    def dfs(node, path):
        if node in path:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        for dep in graph.get(node, []):
            dfs(dep, path + [node])
    
    for node in graph:
        dfs(node, [])
    
    return cycles

def format_graph_ascii(graph: dict[str, list[str]]) -> str:
    lines = ["Bağımlılık Grafiği:"]
    for module, deps in sorted(graph.items()):
        short = module.split(".")[-1]
        lines.append(f"{short}:")
        for dep in deps[:3]:
            lines.append(f"  → {dep.split('.')[-1]}")
        if len(deps) > 3:
            lines.append(f"  → ... +{len(deps)-3} daha")
    return "\n".join(lines)
```

---

## References

- `module-boundary-validation-skill/SKILL.md` — modül sınırları
- `file-dependency-detection-skill/SKILL.md` — import analizi
- `architecture-decision-record-skill/SKILL.md` — ADR
