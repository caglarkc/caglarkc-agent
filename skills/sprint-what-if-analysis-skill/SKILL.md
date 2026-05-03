---
name: sprint-what-if-analysis
description: Planner AI için — "şu olursa ne olur?" sorusunu sprint planına uygulamak; risk senaryolarını simüle etmek.
---

## Purpose

Tek senaryo planlama kırılgan — bir şey yanlış giderse plan çöker.
What-if analizi: "LLM timeout olursa", "kritik dosya başarısız olursa" senaryoları önceden düşünülür.
Her senaryo için acil eylem planı hazırlanır.

---

## When to Apply

- Sprint planı onaylanmadan önce risk analizi istendiğinde
- Kritik bağımlılıklar varken
- Kullanıcı "en kötü senaryo ne?" diye sorduğunda

---

## Rules

- Senaryo: max 3 (fazlası analiz felci yaratır).
- Her senaryo: olasılık (düşük/orta/yüksek), etki, acil plan.
- Yüksek olasılık + yüksek etki: sprint planına dahil edilir.
- Çıktı: kullanıcıya soru olarak sunulur, onay beklenir.

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class RiskScenario:
    name:        str
    probability: str   # "low" | "medium" | "high"
    impact:      str   # "low" | "medium" | "high"
    description: str
    mitigation:  str

COMMON_RISK_SCENARIOS = [
    RiskScenario(
        name="LLM Timeout",
        probability="medium",
        impact="medium",
        description="Birincil LLM 60s içinde yanıt vermez.",
        mitigation="Fallback chain: Gemini → OpenRouter → Ollama",
    ),
    RiskScenario(
        name="Kritik Dosya Başarısız",
        probability="low",
        impact="high",
        description="Bağımlı dosyaların dayandığı temel dosya üretilemez.",
        mitigation="Bağımlı görevler otomatik ertelenir, kullanıcı bildirilir.",
    ),
    RiskScenario(
        name="Token Bütçesi Aşımı",
        probability="medium",
        impact="medium",
        description="Sprint kapsamı tahmininden büyük, token tükenir.",
        mitigation="Token sayacı %80'de uyarır, %100'de sprint duraklatılır.",
    ),
]

def assess_sprint_risks(tasks: list[dict]) -> list[RiskScenario]:
    risks = list(COMMON_RISK_SCENARIOS)
    
    # Çok sayıda görev varsa kapsam riski ekle
    if len(tasks) > 15:
        risks.append(RiskScenario(
            name="Kapsam Kayması",
            probability="high",
            impact="medium",
            description=f"{len(tasks)} görev planlandı — tahminin üzerine çıkabilir.",
            mitigation="Görevler önceliklendirilir, düşük öncelikli ertelenir.",
        ))
    
    return risks

def format_risk_report(risks: list[RiskScenario]) -> str:
    HIGH = [r for r in risks if r.impact == "high" and r.probability == "high"]
    lines = ["Risk Analizi:"]
    for r in risks:
        flag = "🔴" if r.impact == "high" else ("🟡" if r.impact == "medium" else "🟢")
        lines.append(f"  {flag} {r.name} (olasılık: {r.probability})")
        lines.append(f"     Önlem: {r.mitigation}")
    return "\n".join(lines)
```

---

## References

- `sprint-blocker-resolution-skill/SKILL.md` — blocker çözümü
- `cascading-failure-prevention-skill/SKILL.md` — hata yayılma
- `sprint-resource-limits-skill/SKILL.md` — kaynak sınırları
