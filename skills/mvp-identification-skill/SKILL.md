---
name: mvp-identification
description: Planner AI için — bir özellik veya proje için minimum çalışan ve değer üreten seti belirlemek; fazla mühendislik yapmadan işlevselliği teslim etmek.
---

## Purpose

"Ne olmazsa olmaz?" sorusunu yanıtlar.
Fazla mühendislik ve spekülatif özelliklerin önüne geçer.
İlk teslim edilebilir versiyonu mümkün olan en kısa sürede ortaya çıkarır.

---

## When to Apply

- Yeni bir özellik planlanmaya başladığında
- Sprint kapsamı çok büyük göründüğünde
- Kullanıcı tüm detayları aynı anda istediğinde
- "Basit bir versiyonla başlayalım mı?" kararı gerektiğinde

---

## Rules

- MVP = sistemin temel akışını çalıştıran minimum kod seti.
- "Güzel olur" özellikleri MVP'nin dışındadır.
- MVP sonrası iterasyon olacak şekilde plan yapılır.
- Error handling MVP'ye dahil: çökmeden çalışmak zorunlu.
- Logging MVP'ye dahil: neyin olduğunu görmek zorunlu.
- UI güzelliği, optimizasyon, edge case tam coverage MVP dışı.

---

## Guidelines

MVP sınırı çizme soruları:
1. Bu olmadan temel akış çalışır mı? → Evet ise MVP dışı.
2. Bu olmadan sistem çöker mi? → Evet ise MVP içi.
3. Bu olmadan kullanıcı değer alır mı? → Hayır ise MVP dışı.

Bu proje için MVP hiyerarşisi:
```
Katman 1 (her zaman MVP):
- Async çalışma
- Type hint
- Temel hata handling
- Event emit

Katman 2 (genellikle MVP):
- Retry mantığı
- Fallback
- Temel logging

Katman 3 (MVP sonrası):
- Performans optimizasyonu
- Kapsamlı test coverage
- UI iyileştirmesi
- İstatistik/metrik
```

---

## Examples

```
Talep: "Planner'a çok gelişmiş hata raporlama ekle — detaylı stack trace, kullanıcı bildirimi, Telegram mesajı, retry öneri sistemi"

MVP:
✓ Hata log'a yazılır (structured)
✓ State'e errors listesine eklenir
✓ Kullanıcıya kısa hata mesajı

MVP Sonrası (2. sprint):
- Telegram bildirimi
- Retry öneri sistemi
- Stack trace UI'da gösterim
```

---

## References

- `scope-boundary-detection-skill/SKILL.md` — kapsam sınırı
- `priority-ordering-skill/SKILL.md` — önceliklendirme
- `incremental-delivery-planning-skill/SKILL.md` — artımlı teslimat
