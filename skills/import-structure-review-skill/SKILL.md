---
name: import-structure-review
description: Planner AI için — import listesinin doğru sıralanıp sıralanmadığını, kullanılmayan import'ların bulunup bulunmadığını ve circular import riski taşıyıp taşımadığını review sırasında kontrol etmek.
---

## Purpose

Import sorunlarını erken yakalar.
Kullanılmayan import'lar kod kirliliği yaratır.
Circular import'lar runtime'da `ImportError` veya davranış bozukluğuna yol açar.
Yanlış import yolu kırık modüle işaret eder.

---

## When to Apply

- Her Python dosyası review edilirken
- Yeni modül oluşturulurken
- Refactoring sonrası

---

## Rules

- Import sırası: stdlib → üçüncü taraf → proje içi (her grup boş satırla ayrılır).
- Kullanılmayan import'lar kaldırılmalı.
- `from X import *` yasak.
- Circular import: A → B → A (her ikisi de birbirini import ediyor) tespit edilmeli.
- Tip-only import'lar `if TYPE_CHECKING:` bloğunda.
- Proje içi import'lar absolute path ile (`from src.core.event_bus import ...`).

---

## Guidelines

Import sırası örneği:
```python
# stdlib
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# üçüncü taraf
import aiosqlite
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# proje içi
from src.config.settings import get_settings
from src.core.event_bus import get_event_bus
from src.storage.models import FileRecord

# tip-only (runtime'da import edilmez)
if TYPE_CHECKING:
    from src.graph.state import OrchestratorState
```

Circular import tespiti:
```
src/core/event_bus.py → src/graph/state.py import ediyor
src/graph/state.py → src/core/event_bus.py import ediyor
= CIRCULAR! Çözüm: TYPE_CHECKING bloğu veya lazy import
```

Kullanılmayan import tespiti:
```python
import os  # os. hiçbir yerde kullanılmıyor → kaldır
from typing import List  # List kullanılmıyor, list var → kaldır
```

---

## References

- `module-boundary-validation-skill/SKILL.md` — katman uyumu
- `dead-code-detection-skill/SKILL.md` — kullanılmayan kod
- `project-architecture-skill/SKILL.md` — modül yapısı
