---
name: sprint-dependency-graph
description: Planner AI için — sprint görevleri arasındaki bağımlılıkları yönlü çizge olarak temsil etmek ve döngü tespit etmek.
---

## Purpose

Bağımlılık listesi büyüdükçe okunması zorlaşır.
Çizge temsili: görevler arası ilişkiyi görsel ve hesaplanabilir yapar.
Döngü tespiti: "A, B'ye bağlı; B, A'ya bağlı" kilitlenmesi önlenir.

---

## When to Apply

- Sprint planı oluşturulurken bağımlılıklar kontrol edilirken
- Topolojik sıralama yapılmadan önce
- "Neden bu görev başlamıyor?" sorusu araştırılırken

---

## Rules

- Çizge: DAG (yönlü, döngüsüz) olmalı.
- Döngü tespit edilirse: sprint planlanmaz, kullanıcıya bildirilir.
- Kritik yol: en uzun bağımlılık zinciri hesaplanır.
- Çizge: JSON adjacency listesi olarak state'e eklenir.

---

## Guidelines

```python
from collections import defaultdict, deque

def build_dependency_graph(tasks: list[dict]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        task_id = task["id"]
        graph[task_id]  # ensure node exists
        for dep in task.get("depends_on", []):
            graph[dep].append(task_id)
    return dict(graph)

def detect_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    visited = set()
    rec_stack = set()
    cycles = []
    
    def dfs(node: str, path: list[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
        
        path.pop()
        rec_stack.discard(node)
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles

def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    in_degree = defaultdict(int)
    for node, neighbors in graph.items():
        for n in neighbors:
            in_degree[n] += 1
    
    queue = deque(n for n in graph if in_degree[n] == 0)
    order = []
    
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return order

def find_critical_path(graph: dict[str, list[str]], durations: dict[str, int]) -> list[str]:
    # En uzun yolu DFS ile bul
    memo = {}
    def longest(node):
        if node in memo:
            return memo[node]
        children = graph.get(node, [])
        if not children:
            memo[node] = ([node], durations.get(node, 0))
            return memo[node]
        best_path, best_len = [node], durations.get(node, 0)
        for child in children:
            child_path, child_len = longest(child)
            total = durations.get(node, 0) + child_len
            if total > best_len:
                best_path = [node] + child_path
                best_len  = total
        memo[node] = (best_path, best_len)
        return memo[node]
    
    roots = [n for n in graph if all(n not in v for v in graph.values())]
    if not roots:
        return []
    best = max((longest(r) for r in roots), key=lambda x: x[1])
    return best[0]
```

---

## References

- `task-dependency-ordering-skill/SKILL.md` — bağımlılık sıralaması
- `dependency-graph-visualization-skill/SKILL.md` — bağımlılık görselleştirme
- `sprint-conflict-resolution-skill/SKILL.md` — çakışma çözümü
