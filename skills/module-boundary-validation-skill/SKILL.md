---
name: module-boundary-validation
description: Planner AI için — kod review sırasında her modülün kendi sorumluluğu dışına çıkıp çıkmadığını kontrol etmek; katman ihlallerini tespit etmek.
---

## Purpose

Her modülün sadece kendi katmanındaki işi yapmasını sağlar.
Interface'in direkt DB'ye erişmesi, node'un başka node'u çağırması gibi ihlalleri yakalar.
Mimari bütünlüğü korur.

---

## When to Apply

- Coder AI kodu review edilirken
- Yeni dosya planlanırken "bu nereye gider?" sorusunda
- Import listesi incelenirken
- Refactoring sprint'i planlanırken

---

## Rules

- `src/interfaces/` → sadece EventBus ile iletişim, direkt LangGraph erişimi yasak.
- `src/graph/nodes/` → sadece state oku/yaz, direkt DB erişimi yasak.
- `src/storage/` → sadece DB operasyonları, iş mantığı yasak.
- `src/core/` → servisler burada, interface'e bağımlı olmamalı.
- `src/config/` → sadece settings, başka hiçbir modülü import etmez.
- Çapraz katman import = ihlal.

---

## Guidelines

Katman haritası ve izin verilen import'lar:
```
src/config/          → hiçbir şeyi import etmez
src/storage/         → config import edebilir
src/core/            → config + storage import edebilir
src/graph/           → config + storage + core import edebilir
src/interfaces/      → config + core (EventBus) import edebilir

YASAK:
src/graph/nodes/ → src/interfaces/ import edemez
src/storage/ → src/graph/ import edemez
src/interfaces/ → src/graph/ direkt import edemez
```

İhlal tespiti:
```python
# src/interfaces/telegram/bot.py içinde
from src.graph.graph_manager import GraphManager  # İHLAL!
# Doğrusu:
from src.core.event_bus import get_event_bus  # OK
```

Review kontrol sorusu: "Bu dosya neden bu import'a ihtiyaç duyuyor? Başka katmanın işini mi yapıyor?"

---

## Examples

```
Coder AI çıktısı review:

src/graph/nodes/planner.py içinde:
from src.interfaces.telegram.notifier import send_message  # İHLAL

Düzeltme:
event_bus.emit("plan.generated", {...})  # event bus üzerinden
Telegram subscriber event'i yakalar — planner Telegram'ı bilmez
```

---

## References

- `project-architecture-skill/SKILL.md` — katman haritası
- `interface-contract-review-skill/SKILL.md` — interface sözleşmeleri
- `coupling-analysis-skill/SKILL.md` — bileşen bağlantıları
