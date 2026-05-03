---
name: sprint-diff-report
description: Planner AI için — sprint öncesi ve sonrası dosya değişikliklerini karşılaştıran rapor oluşturmak.
---

## Purpose

Sprint bitti ama ne değişti tam bilinmiyor.
Diff raporu, hangi dosyaların eklendiğini, değiştirildiğini veya silindiğini gösterir.
Kullanıcıya ve reviewer'a net görünürlük sağlar.

---

## When to Apply

- Sprint tamamlandığında kullanıcıya özet sunulurken
- Reviewer node çıktıyı doğrularken
- Sprint retrospective'inde değişim analizi yapılırken

---

## Rules

- Sadece sprint kapsamındaki dosyalar listelenir.
- Değişim türleri: added, modified, deleted, unchanged.
- Her dosya için satır sayısı değişimi (+N / -M) gösterilir.
- Büyük diff: dosya başına özet, tam içerik değil.

---

## Guidelines

```python
from dataclasses import dataclass
from pathlib import Path
import difflib

@dataclass
class FileDiff:
    path: str
    status: str  # "added" | "modified" | "deleted" | "unchanged"
    lines_added: int = 0
    lines_removed: int = 0

def compute_file_diff(
    before_content: str | None,
    after_content: str | None,
    file_path: str,
) -> FileDiff:
    if before_content is None and after_content is not None:
        return FileDiff(file_path, "added", len(after_content.splitlines()), 0)
    if before_content is not None and after_content is None:
        return FileDiff(file_path, "deleted", 0, len(before_content.splitlines()))
    if before_content == after_content:
        return FileDiff(file_path, "unchanged")
    
    diff = list(difflib.unified_diff(
        before_content.splitlines(),
        after_content.splitlines(),
    ))
    added   = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
    return FileDiff(file_path, "modified", added, removed)

def format_sprint_diff_report(diffs: list[FileDiff]) -> str:
    added    = [d for d in diffs if d.status == "added"]
    modified = [d for d in diffs if d.status == "modified"]
    deleted  = [d for d in diffs if d.status == "deleted"]
    
    lines = ["## Sprint Değişim Raporu", ""]
    if added:
        lines.append(f"### Eklenen ({len(added)} dosya)")
        for d in added:
            lines.append(f"  + {d.path} (+{d.lines_added} satır)")
    if modified:
        lines.append(f"\n### Değiştirilen ({len(modified)} dosya)")
        for d in modified:
            lines.append(f"  ~ {d.path} (+{d.lines_added}/-{d.lines_removed})")
    if deleted:
        lines.append(f"\n### Silinen ({len(deleted)} dosya)")
        for d in deleted:
            lines.append(f"  - {d.path}")
    return "\n".join(lines)
```

---

## References

- `state-snapshot-diff-skill/SKILL.md` — state diff
- `code-diff-generation-skill/SKILL.md` — kod diff üretimi
- `sprint-completion-celebration-skill/SKILL.md` — tamamlanma mesajı
