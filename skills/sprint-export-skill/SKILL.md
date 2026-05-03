---
name: sprint-export
description: Planner AI için — sprint planını ve sonuçlarını JSON veya Markdown formatında dışa aktarmak; arşivleme ve paylaşım için.
---

## Purpose

Sprint sonuçları paylaşılmak veya arşivlenmek istenebilir.
Export, sprint'i sistemden bağımsız okunabilir formata çevirir.
Kullanıcı "bunu kaydet" dediğinde hızlıca dosya üretilir.

---

## When to Apply

- Kullanıcı "rapor al", "export et", "kaydet" dediğinde
- Sprint arşivlenirken
- Başka bir sisteme aktarım gerektiğinde

---

## Rules

- JSON: makine okunabilir, tam veri.
- Markdown: insan okunabilir, özet.
- Export dosyası: `exports/sprint_<id>_<date>.md` veya `.json`.
- Gizli veri (API key) export'a dahil edilmez.

---

## Guidelines

```python
import json
from datetime import datetime

async def export_sprint_markdown(
    sprint: Sprint,
    decisions: list[Decision],
    output_dir: str = "exports",
) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.utcnow().strftime("%Y%m%d")
    filename = f"{output_dir}/sprint_{sprint.sprint_id[:8]}_{date_str}.md"
    
    registry = sprint.file_registry or {}
    done = [f for f, s in registry.items() if s == "done"]
    failed = [f for f, s in registry.items() if s == "failed"]
    
    lines = [
        f"# Sprint Raporu: {sprint.sprint_id}",
        f"Tarih: {date_str}",
        f"Durum: {sprint.status}",
        "",
        "## Özet",
        sprint.summary or "Özet yok",
        "",
        f"## Tamamlanan Dosyalar ({len(done)})",
    ]
    lines.extend(f"- `{f}`" for f in sorted(done))
    
    if failed:
        lines.append(f"\n## Başarısız Dosyalar ({len(failed)})")
        lines.extend(f"- `{f}`" for f in sorted(failed))
    
    if decisions:
        lines.append("\n## Alınan Kararlar")
        for d in decisions:
            lines.append(f"- **{d.summary}**")
    
    content = "\n".join(lines)
    async with aiofiles.open(filename, "w") as f:
        await f.write(content)
    
    logger.info(f"Sprint export edildi: {filename}")
    return filename
```

PM mesaj:
```
[SOHBET] Sprint raporu oluşturuldu:

Dosya: exports/sprint_abc123_20260501.md

İçerik:
- 8 tamamlanan dosya
- 0 başarısız dosya
- 3 karar kaydı
```

---

## References

- `sprint-summary-generation-skill/SKILL.md` — özet
- `decision-log-maintenance-skill/SKILL.md` — kararlar
- `async-context-manager-skill/SKILL.md` — dosya yazma
