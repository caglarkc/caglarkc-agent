---
name: task-granularity-calibration
description: Planner AI için — Coder AI'a verilen görevlerin ne çok büyük ne de çok küçük olduğunu garantilemek; doğru boyutlandırma ile tek seferde başarıyla tamamlanabilir görevler üretmek.
---

## Purpose

Görev boyutunu Coder AI'ın verimli çalışabileceği şekilde kalibre eder.
Çok büyük görev → parçalanmamış context, hata riski.
Çok küçük görev → fazla overhead, koordinasyon maliyeti.

---

## When to Apply

- Worker'a görev yazılmadan önce
- Bir görev 3'ten fazla fonksiyon içeriyorsa kontrol et
- Bir görev birden fazla sorumluluk taşıyorsa kontrol et
- Sprint içindeki tüm görevlerin boyutu dengeli mi değerlendir

---

## Rules

- Tek görev: 1 dosya veya 3'e kadar yakın ilişkili dosya.
- Tek görev: maksimum 5 yeni fonksiyon veya 150 satır yeni kod tahmini.
- "Ve ayrıca" içeren görev → ikiye böl.
- Test dosyası ayrı görev.
- Config/env değişikliği ayrı mini görev veya ilgili görevin kısıtına ekle.

---

## Guidelines

Boyut kontrol soruları:
1. Bu görevi bitirmek için kaç farklı şeyi anlamak gerekiyor? → 3'ten fazlaysa böl.
2. Görev açıklaması tek cümleyle özetlenebiliyor mu? → Hayırsa böl.
3. Başarısız olursa tam olarak nerede bozuldu anlaşılabilir mi? → Hayırsa böl.

Boyut şablonları:

**Mikro görev** (30 dakika):
- Tek fonksiyona parametre ekle
- Var olan log mesajını düzelt
- Tek config alanı ekle

**Normal görev** (2-4 saat):
- Yeni node implementasyonu (1 dosya)
- Mevcut servise yeni method ekle
- DB tablosuna yeni alan + migration

**Büyük görev** (böl):
- Yeni entegrasyon (3+ dosya)
- Mimari değişiklik
- Sprint olarak planla, görev olarak verme

---

## Examples

```
YANLIŞ (çok büyük):
"Planner node'u yeniden yaz, retry ekle, yeni event emit et,
test yaz ve Telegram bildirimi entegre et"

DOĞRU (4 ayrı görev):
Görev 1: planner.py — LLM retry mantığı (tek fonksiyon)
Görev 2: planner.py — yeni event emit (2 satır)
Görev 3: tests/test_planner.py — retry test
Görev 4: telegram/notifier.py — planner event subscription
```

---

## References

- `user-story-decomposition-skill/SKILL.md` — bölme stratejisi
- `file-dependency-graph-design-skill/SKILL.md` — bağımlılıklar
- `worker-load-balancing-strategy-skill/SKILL.md` — worker dağılımı
