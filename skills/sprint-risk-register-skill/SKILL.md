---
name: sprint-risk-register
description: Planner AI için — sprint boyunca tespit edilen riskleri kayıt altında tutmak; her riske önlem ve sahip atamak.
---

## Purpose

Riskler ağızdan çıkıp unutulur.
Risk kaydı: tespit edilen her riski ID'li, öncelikli, sahipli kayıt eder.
Sprint sonunda hangi riskler gerçekleşti, hangisi önlendi görülür.

---

## When to Apply

- Sprint what-if analizi sırasında
- Blocker tespit edildiğinde risk olarak kayıt edilirken
- Sprint sonrası retrospective hazırlanırken

---

## Rules

- Her risk: ID, açıklama, olasılık, etki, önlem, durum.
- Durum: open → mitigated | realized | closed.
- Risk sayısı: sprint başına maks 10.
- Gerçekleşen risk: incident olarak ayrıca loglanır.

---

## Guidelines

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Risk:
    risk_id:     str
    description: str
    probability: str  # low | medium | high
    impact:      str  # low | medium | high
    mitigation:  str
    status:      str = "open"
    created_at:  str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: str | None = None

def add_risk(state: dict, description: str, probability: str,
             impact: str, mitigation: str) -> dict:
    risks = list(state.get("risk_register", []))
    risk  = Risk(
        risk_id=f"R{len(risks)+1:03d}",
        description=description,
        probability=probability,
        impact=impact,
        mitigation=mitigation,
    )
    risks.append(risk.__dict__)
    return {"risk_register": risks}

def update_risk_status(state: dict, risk_id: str, new_status: str) -> dict:
    risks = list(state.get("risk_register", []))
    for r in risks:
        if r["risk_id"] == risk_id:
            r["status"] = new_status
            if new_status in ("mitigated", "realized", "closed"):
                r["resolved_at"] = datetime.utcnow().isoformat()
    return {"risk_register": risks}

def format_risk_register(risks: list[dict]) -> str:
    if not risks:
        return "Risk kaydı boş."
    lines = ["Risk Kaydı:"]
    for r in risks:
        flag = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(r["impact"], "⚪")
        lines.append(f"  {flag} [{r['risk_id']}] {r['description'][:50]} — {r['status'].upper()}")
    return "\n".join(lines)
```

---

## References

- `sprint-what-if-analysis-skill/SKILL.md` — what-if analizi
- `sprint-blocker-resolution-skill/SKILL.md` — blocker çözümü
- `architecture-decision-record-skill/SKILL.md` — mimari karar kaydı
