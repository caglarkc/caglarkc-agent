---
name: sprint-goal-articulation
description: Planner AI için — her sprint için tek cümlelik net bir hedef ve başarı tanımı yazmak; ekibin ne yapmaya çalıştığını herkesin anlayacağı şekilde ifade etmek.
---

## Purpose

Sprint'in neden var olduğunu tek cümleyle özetler.
Review ve onay aşamasında "amaca ulaşıldı mı?" sorusunu yanıtlar.
Coder AI'ın önceliğini kaybetmesini önler.

---

## When to Apply

- Her yeni sprint başlamadan önce
- Onay isteği hazırlanırken
- Sprint review'da değerlendirme yapılırken
- Sprint yön değiştirdiğinde revize edilirken

---

## Rules

- Sprint hedefi 1 cümle, maksimum 20 kelime.
- "Ne yapılacak" değil "ne elde edilecek" perspektifinden yazılır.
- Teknik jargon kullanılmaz — kullanıcının anlayacağı dil.
- Hedef değişirse sprint onayı iptal, yeni onay alınır.
- Kabul kriterleriyle doğrudan bağlantılı olmalı.

---

## Guidelines

Hedef yazım kalıpları:
```
KÖTÜ: "planner.py'e retry ekle ve state.py'i güncelle"
İYİ: "Planner hata aldığında otomatik olarak 3 kez dener"

KÖTÜ: "Telegram modülünü refactor et"
İYİ: "Telegram bildirimleri kullanıcı planı onayladığında anında ulaşır"

KÖTÜ: "Birçok şeyi iyileştir"
İYİ: "Sistem çöktükten sonra kaldığı yerden devam eder"
```

Sprint hedefi ile kabul kriteri bağlantısı:
```
Hedef: "Worker başarısız olduğunda sistem otomatik yeniden dener"

Kabul Kriterleri:
✓ Worker 3 kez retry yapar (exponential backoff)
✓ 3 denemeden sonra worker_failure_log'a kaydeder
✓ Kullanıcıya başarısızlık bildirimi gönderilir
✓ Diğer worker'lar etkilenmez
```

---

## Examples

```
Sprint içeriği:
- planner.py'e retry decorator
- worker_failure_log'a kayıt
- Telegram bildirim

Sprint hedefi:
"LLM çağrısı başarısız olduğunda sistem sessizce yeniden dener, 
kullanıcıya sadece gerçek başarısızlık bildirilir"
```

---

## References

- `acceptance-criteria-definition-skill/SKILL.md` — başarı kriterleri
- `sprint-size-estimation-skill/SKILL.md` — sprint boyutu
- `pm-mode-skill/SKILL.md` — onay-bekle formatı
