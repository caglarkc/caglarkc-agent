---
name: single-responsibility-enforcement
description: Coder AI için — her modül, sınıf ve fonksiyonun tek bir sorumluluğa sahip olmasını sağlamak; birden fazla işi yapan bileşenleri tespit ve ayırmak.
---

## Purpose

Kod değişikliğinin sınırlı bir alanı etkilemesini sağlar.
Birden fazla sorumluluklu modüller hem test etmesi hem de değiştirmesi zordur.
"Bu değişince ne bozulur?" sorusunun cevabı kısa tutulur.

---

## When to Apply

- Yeni sınıf veya modül tasarlanırken
- Mevcut fonksiyon çok iş yapıyor gibi görünüyorsa
- Import listesi çok uzunsa (çok bağımlılık = çok sorumluluk işareti)

---

## Rules

- Sınıf: tek bir sorumluluk, tek bir değişim nedeni.
- Fonksiyon: tek bir şeyi yapar, isminde "ve" varsa böl.
- Modül: tek bir domain (storage, events, planning...).
- `EventBus` sadece event routing yapar — iş mantığı içermez.
- `StateManager` sadece state saklar/okur — iş mantığı içermez.
- Node'lar sadece orchestration yapar — iş mantığı servis katmanında.

---

## Guidelines

Sorumluluk tespiti:
```
"Bu sınıf/fonksiyon neden değişir?" → birden fazla cevap → böl

Kötü örnekler:
class PlannerService:  # ← 5 sorumluluk
    def plan_and_save_and_notify_and_validate_and_log(self, task):
        ...

def process_message(message):
    # mesajı parse et VE
    # veritabanına kaydet VE
    # telegram'a gönder VE
    # log'a yaz
    # ← 4 sorumluluk

İyi örnekler:
class ManagerPlanningService:
    """Sadece LLM ile plan üretmekten sorumlu."""
    async def process_turn(self, message: str, history: list) -> PlanResult:
        ...

class SprintRepository:
    """Sadece sprint DB operasyonlarından sorumlu."""
    async def create_sprint(self, sprint: Sprint) -> None:
        ...

class TelegramNotifier:
    """Sadece Telegram mesajı göndermekten sorumlu."""
    async def send_approval_request(self, approval: ApprovalRequest) -> None:
        ...
```

Node içinde iş mantığı yasak:
```python
# YANLIŞ — node içinde iş mantığı
async def planner_node(state):
    # 50 satır LLM çağrısı, parse, validation...
    
# DOĞRU — node ince wrapper, iş serviste
async def planner_node(state):
    result = await manager_service.process_turn(...)  # iş burada
    return {"draft_plan": result.plan}
```

---

## References

- `function-length-review-skill/SKILL.md` — fonksiyon boyutu
- `module-boundary-validation-skill/SKILL.md` — katman sınırları
- `dry-principle-enforcement-skill/SKILL.md` — tekrar
