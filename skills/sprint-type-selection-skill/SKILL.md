---
name: sprint-type-selection
description: Planner AI için — bir işin "contract" sprint mi yoksa "feature" sprint mi olacağını belirlemek; sprint türüne göre planlama stratejisini ayarlamak.
---

## Purpose

Her sprint başlamadan önce doğru türde planlanmasını sağlar.
Contract sprint interface'leri ve type'ları önce kurar; feature sprint iş mantığını uygular.
Yanlış sprint türü seçimi dosya bağımlılıklarını bozar.

---

## When to Apply

- Her yeni sprint planlanmadan önce
- Yeni bir modül veya bileşen oluşturulacağında
- Mevcut koda büyük ekleme yapılacağında

---

## Rules

- **Contract sprint**: Sadece `src/graph/state.py`, Pydantic modeller, Protocol tanımları, interface dosyaları. Çalışan kod yok, sadece tip ve kontrat.
- **Feature sprint**: Contract sprint tamamlandıktan sonra, iş mantığı, async operasyonlar, DB yazma.
- Contract sprint feature sprint'ten önce gelmeli eğer yeni state alanı veya model gerekiyorsa.
- Sadece mevcut dosyaya ekleme yapılıyorsa (yeni model yok) → doğrudan feature sprint.
- Her sprint türü için farklı review kriterleri uygulanır.

---

## Guidelines

Sprint türü karar ağacı:
```
Yeni OrchestratorState alanı gerekiyor mu?
  Evet → Contract sprint önce (state.py güncelleme)
  Hayır →
    Yeni Pydantic model/Protocol gerekiyor mu?
      Evet → Contract sprint önce
      Hayır → Feature sprint direkt başlar
```

Contract sprint içeriği:
- `src/graph/state.py` → yeni TypedDict alanları
- `src/storage/models.py` → yeni Pydantic modeller
- `src/core/contracts.py` → event/approval contract güncellemeleri
- Çalışan kod yok, sadece type definitions

Feature sprint içeriği:
- Node implementasyonu
- Core servis mantığı
- DB operasyonları
- Event emit/subscribe

Review farkı:
- Contract sprint: type correctness, naming, backwards compatibility
- Feature sprint: async correctness, hata handling, state update doğruluğu

---

## Examples

```
Talep: "Worker'a metadata alanı ekle ve bunu DB'ye kaydet"

Karar:
- OrchestratorState'e yeni alan → Contract sprint gerekli
- DB'ye yazma → Feature sprint

Sprint A (Contract): state.py + models.py güncellemesi
Sprint B (Feature): worker.py + repository.py güncellemesi
Bağımlılık: B → A'ya bağımlı
```

---

## References

- `file-dependency-graph-design-skill/SKILL.md` — bağımlılık sırası
- `sprint-goal-articulation-skill/SKILL.md` — sprint hedefi
- `project-architecture-skill/SKILL.md` — mimari katmanlar
