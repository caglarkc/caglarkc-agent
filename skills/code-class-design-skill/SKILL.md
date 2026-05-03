---
name: code-class-design
description: Coder AI için — Python sınıfı tasarlarken sorumlulukları netleştirmek; SRP, composition over inheritance prensiplerini uygulamak.
---

## Purpose

LLM büyük, çok sorumluluğu olan sınıflar üretebilir.
İyi sınıf tasarımı: tek sorumluluk, bağımlılık enjeksiyonu, test edilebilirlik.
Composition tercih edilir — derin kalıtım hiyerarşisi kaçınılır.

---

## When to Apply

- Yeni servis veya yönetici sınıfı oluşturulurken
- Kod inceleme sırasında "bu sınıf çok büyük" görüldüğünde
- Refactor: bir sınıfı daha küçük parçalara bölerken

---

## Rules

- Tek sorumluluk: bir sınıf bir şey yapar.
- Bağımlılıklar: `__init__` parametresi olarak alınır (DI).
- Kalıtım: maks 2 seviye — composition tercih edilir.
- `__init__`: iş mantığı yok, sadece atamalar.

---

## Guidelines

```python
from dataclasses import dataclass
from typing import Protocol

# Kötü: çok büyük, çok sorumlu
class BadSprintManager:
    def __init__(self):
        self.db = sqlite3.connect("sprint.db")
        self.llm = ChatGoogleGenerativeAI(...)
        self.tasks = []
        self.metrics = {}
    
    def plan(self): ...
    def execute(self): ...
    def validate(self): ...
    def notify(self): ...
    def report(self): ...

# İyi: sorumluluklar ayrılmış, DI ile bağımlılıklar

class LLMClient(Protocol):
    async def invoke(self, messages: list) -> str: ...

class SprintRepository(Protocol):
    async def save(self, sprint: dict) -> None: ...
    async def load(self, sprint_id: str) -> dict | None: ...

@dataclass
class SprintPlanner:
    llm:  LLMClient
    repo: SprintRepository
    
    async def create_plan(self, goal: str) -> dict:
        # Sadece planlama sorumluluğu
        ...

@dataclass
class SprintExecutor:
    llm:  LLMClient
    repo: SprintRepository
    
    async def execute_task(self, task: dict) -> dict:
        # Sadece yürütme sorumluluğu
        ...

@dataclass
class SprintReporter:
    repo: SprintRepository
    
    async def generate_report(self, sprint_id: str) -> str:
        # Sadece raporlama sorumluluğu
        ...

# Koordinasyon: orkestratör bileşenleri birleştirir
@dataclass
class SprintOrchestrator:
    planner:  SprintPlanner
    executor: SprintExecutor
    reporter: SprintReporter
```

---

## References

- `dependency-injection-patterns-skill/SKILL.md` — bağımlılık enjeksiyonu
- `abstract-base-class-skill/SKILL.md` — soyut temel sınıf
- `schema-first-design-skill/SKILL.md` — şema öncelikli tasarım
