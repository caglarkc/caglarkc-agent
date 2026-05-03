---
name: incremental-delivery-planning
description: Planner AI için — her sprint sonunda kullanıcıya somut değer teslim etmek; "hep ya da hiç" yerine kademeli ilerleme planlamak.
---

## Purpose

Her sprint'in bağımsız bir değer birimi teslim etmesini sağlar.
"Sprint 3 bitmeden hiçbir şey çalışmaz" durumunu önler.
Kullanıcının her aşamada ilerlemeyi görmesini sağlar.

---

## When to Apply

- Çok adımlı proje planlanırken
- Sprint'ler arasında sıralama yapılırken
- Kullanıcıya ne zaman sonuç görebileceği sorulduğunda

---

## Rules

- Her sprint'in sonunda en az bir "görülebilir" çıktı olmalı.
- Core infrastructure sprint'leri en fazla 2 arka arkaya gelebilir.
- Demo edilebilir özellik sprint'leri arasına sıkıştırılır.
- Her sprint'in "Tamamlandı" kriteri kullanıcı perspektifinden tanımlanır.
- "Şimdi ne çalışıyor?" sorusuna her sprint sonunda yanıt verilebilmeli.

---

## Guidelines

Teslimat piramidi:
```
Sprint 1: Çalışan temel akış (minimum)
Sprint 2: Hata toleransı eklendi
Sprint 3: Yeni özellik A
Sprint 4: Yeni özellik B
Sprint 5: Optimizasyon ve polish
```

Her sprint teslim formatı:
```
SPRINT X SONUCU:
Kullanıcı artık şunu yapabilir: <...>
Öncekinden farkı: <...>
Test edilebilir: <nasıl>
```

İnkremental bölme örüntüsü:
```
YANLIŞ: Tüm sistemin tamamını tek seferde planla
DOĞRU:
  Sprint 1: Planner → plan üretir (Telegram yok, CLI yok)
  Sprint 2: CLI üzerinden görev gönderme
  Sprint 3: Telegram entegrasyonu
  Sprint 4: Retry ve hata recovery
```

---

## References

- `mvp-identification-skill/SKILL.md` — minimum değer seti
- `sprint-goal-articulation-skill/SKILL.md` — sprint hedefi
- `multi-sprint-roadmap-design-skill/SKILL.md` — uzun vadeli plan
