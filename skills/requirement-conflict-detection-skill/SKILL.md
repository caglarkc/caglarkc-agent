---
name: requirement-conflict-detection
description: Planner AI için — birbiriyle çelişen gereksinimleri tespit etmek, önceliklendirmek ve kullanıcıyla çözüme kavuşturmak.
---

## Purpose

Çelişen gereksinimler uygulamaya geçilmeden tespit edilir.
Hangi gereksinimin öncelikli olduğu netleştirilir.
Mimari tutarsızlıklara yol açabilecek çakışmalar erken engellenir.

---

## When to Apply

- Birden fazla gereksinim aynı bileşeni farklı yönde değiştirmeyi gerektiriyorsa
- Performans vs. güvenilirlik gibi trade-off var ise
- Yeni istek mevcut bir kararla çelişiyorsa
- İki sprint'in aynı dosyayı farklı şekillerde değiştirmesi gerekiyorsa

---

## Rules

- Çakışma tespit edildiğinde plan askıya alınır, kullanıcıya bildirilir.
- Otomatik çözüm yapılmaz — kullanıcı hangi gereksinimin öncelikli olduğuna karar verir.
- Çözüm kararı `decision_log`'a yazılır.
- Mimariyle çelişen gereksinim önce fizibilite kontrolünden geçer.

---

## Guidelines

Çakışma tipleri:

**Dosya çakışması**
- İki sprint aynı dosyayı değiştirmek istiyor
- Çözüm: sıralı sprint, ikincisi birincisine bağımlı

**Davranış çakışması**
- Özellik A "sessiz başarısız ol" diyor, özellik B "kullanıcıya bildir" diyor
- Çözüm: hangi durum için hangisi geçerli?

**Mimari çakışma**
- Yeni bileşen event bus'ı bypass ediyor
- Çözüm: kabul edilemez, mimari kural korunur

**Kaynak çakışması**
- İki worker aynı dosyayı yazıyor
- Çözüm: file_registry reservation sistemi, sıralı atama

Çakışma raporu formatı:
```
ÇAKIŞMA TESPİT EDİLDİ:
Gereksinim A: <...>
Gereksinim B: <...>
Çakışma: <nasıl çakışıyor>
Seçenekler:
  1. A öncelikli → B sonraya ertelenir
  2. B öncelikli → A revize edilir
  3. <özel çözüm>
[ONAY-BEKLE] Hangi seçeneği tercih edersiniz?
```

---

## References

- `scope-boundary-detection-skill/SKILL.md` — kapsam sınırları
- `pm-mode-skill/SKILL.md` — onay workflow
- `file-dependency-graph-design-skill/SKILL.md` — dosya bağımlılıkları
