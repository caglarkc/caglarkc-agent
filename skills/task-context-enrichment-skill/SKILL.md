---
name: task-context-enrichment
description: Coder AI için — görev yürütmeden önce ilgili dosya içeriklerini, bağımlılıkları ve proje bağlamını görev nesnesine eklemek.
---

## Purpose

Görev tek başına "X fonksiyonunu yaz" der ama hangi modüle, hangi stile göre bilinmez.
Bağlam zenginleştirme: ilgili dosyaları okur, önceki kararları ekler, görevi tamamlar.
LLM daha iyi üretim yapar çünkü bağlam eksiksizdir.

---

## When to Apply

- Worker node görevi LLM'e göndermeden önce
- Bağımlı dosya içerikleri bilinmesi gerektiğinde
- Projenin mevcut yapısına uyumlu kod üretilirken

---

## Rules

- Eklenen bağlam: maks 3 ilgili dosya (token tasarrufu).
- Dosya içeriği: ilk 100 satır (büyük dosyalar için).
- Bağlam eklenince task nesnesine `enriched: true` işareti konur.
- Hassas dosyalar (.env, credentials) asla eklenmez.

---

## Guidelines

```python
from pathlib import Path

SENSITIVE_PATTERNS = {".env", "credentials", "secret", "private_key"}

def is_sensitive(file_path: str) -> bool:
    path_lower = file_path.lower()
    return any(p in path_lower for p in SENSITIVE_PATTERNS)

def load_file_snippet(file_path: str, max_lines: int = 100) -> str | None:
    p = Path(file_path)
    if not p.exists() or is_sensitive(file_path):
        return None
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    snippet = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        snippet += f"\n... ({len(lines) - max_lines} satır daha)"
    return snippet

def enrich_task(task: dict, project_root: str) -> dict:
    if task.get("enriched"):
        return task
    
    enriched = dict(task)
    context_files = {}
    
    for dep_path in task.get("depends_on_files", [])[:3]:
        full = str(Path(project_root) / dep_path)
        snippet = load_file_snippet(full)
        if snippet:
            context_files[dep_path] = snippet
    
    if context_files:
        enriched["context_files"] = context_files
    enriched["enriched"] = True
    return enriched

def build_enriched_prompt(task: dict) -> str:
    parts = [f"Görev: {task.get('description', '')}"]
    
    for path, content in task.get("context_files", {}).items():
        parts.append(f"\n--- {path} ---\n{content}")
    
    parts.append(f"\nHedef dosya: {task.get('file_path', '')}")
    return "\n".join(parts)
```

---

## References

- `file-context-loader-skill/SKILL.md` — dosya bağlam yükleyici
- `context-injection-strategy-skill/SKILL.md` — bağlam enjeksiyonu
- `worker-node-implementation-skill/SKILL.md` — worker node
