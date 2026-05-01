---
name: non-functional-requirement-extraction
description: Planner AI için — kullanıcının söylemediği ama sistemin karşılaması gereken performans, güvenlik, güvenilirlik ve ölçeklenebilirlik gereksinimlerini ortaya çıkarmak.
---

## Purpose

Fonksiyonel olmayan gereksinimleri planlamaya dahil eder.
"Hızlı olsun", "güvenli olsun" gibi belirsiz ifadeleri ölçülebilir kriterlere dönüştürür.
Bu gereksinimler sprint planında kısıt olarak yer alır.

---

## When to Apply

- Yeni bir proje başlarken
- Performans veya güvenlikle ilgili herhangi bir yorum yapıldığında
- Dış kullanıcıya veya production ortamına gidecek kod planlanırken
- Mevcut bir sistemin iyileştirilmesi istendiğinde

---

## Rules

- "Hızlı" → kaç ms altında? belirsiz kalırsa makul varsayım yap ve not düş.
- Güvenlik gereksinimleri her zaman sorgulanır: API key log'a düşüyor mu?
- Güvenilirlik: Daemon çöktüğünde ne olmalı? Checkpoint'ten resume zorunlu mu?
- Ölçek: Kaç eş zamanlı proje? Kaç worker? Yanıt verme süresi?
- Tüm non-functional gereksinimler sprint kısıtlarına eklenir.

---

## Guidelines

NFR kategorileri ve soru kalıpları:

**Performans**
- LLM yanıt timeout süresi nedir? (varsayılan: 30s)
- DB sorgu süresi beklentisi? (varsayılan: <100ms)
- Graph node execution max süresi?

**Güvenlik**
- API key'ler log'a düşmemeli (zorunlu)
- Kullanıcı input'u SQL injection koruması (zorunlu)
- Path traversal koruması dosya yazarken (zorunlu)

**Güvenilirlik**
- Daemon çöktüğünde pending thread'ler resume edilmeli (zorunlu)
- Worker retry sayısı (varsayılan: 3)
- LLM provider fallback zinciri (zorunlu)

**Gözlemlenebilirlik**
- Rotating file log (zorunlu, 10MB/5 yedek)
- Event bus history (500 event)
- Heartbeat emission (zorunlu)

---

## Examples

```
Kullanıcı: "Sistemi daha güvenilir yap"

Extraction:
- Güvenilirlik: checkpoint resume ✓ (zaten var)
- Worker retry: 3 deneme ✓ (zaten var)
- Eksik: stall detection timeout 600s → kısaltılabilir mi?
- Eksik: worker failure log retention süresi tanımsız

NFR Sprint Kısıtları:
- Worker timeout: 30s per LLM call
- Stall timeout: 300s (mevcut 600s → değiştirilmeli)
- Failure log retention: 30 gün
```

---

## References

- `technical-feasibility-check-skill/SKILL.md` — uygulanabilirlik
- `acceptance-criteria-definition-skill/SKILL.md` — ölçülebilir kriterler
- `project-architecture-skill/SKILL.md` — mevcut güvenilirlik mekanizmaları
