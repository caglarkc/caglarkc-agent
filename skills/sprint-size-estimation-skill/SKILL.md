---
name: sprint-size-estimation
description: Planner AI için — bir sprint'in kaç dosya, kaç görev ve tahminen ne kadar süreceğini belirlemek; aşırı büyük veya anlamsız küçük sprint'leri önlemek.
---

## Purpose

Sprint boyutunu önceden tahmin eder.
Çok büyük sprint'ler → çok uzun review döngüsü, yüksek hata riski.
Çok küçük sprint'ler → verimsizlik, koordinasyon overhead.
İdeal sprint boyutu tek bir review cycle'da tamamlanabilen iş.

---

## When to Apply

- Yeni sprint planlanmaya başlandığında
- Kullanıcının isteği birden fazla dosyayı kapsıyorsa
- "Bu kaç sprint sürer?" sorusu sorulduğunda

---

## Rules

- İdeal sprint: 3-7 dosya, 1-3 gün.
- Maksimum sprint: 10 dosya. Daha büyükse 2 sprint'e böl.
- Minimum anlamlı sprint: kullanıcıya gösterilebilir değer üreten iş.
- Review cycle sayısı maksimum 3 olmalı. Fazlası → sprint çok büyük.
- Her sprint tek bir tema altında toplanabilmeli.

---

## Guidelines

Boyut hesaplama:
```
Dosya sayısı × ortalama karmaşıklık → tahmini süre

Karmaşıklık çarpanları:
- Yeni node (high): 4 saat
- Yeni servis metodu (medium): 2 saat
- Config değişikliği (low): 30 dakika
- Test dosyası (medium): 1.5 saat

Sprint toplam: tüm görevlerin toplamı ÷ paralellik faktörü
```

Sprint bölme kararı:
```
< 3 görev → belki başka sprint'e ekle veya direkt yap
3-7 görev → ideal sprint
7-10 görev → büyük ama kabul edilebilir
> 10 görev → kesinlikle 2 sprint'e böl
```

Sprint temaları (iyi örnekler):
- "Planner retry ve hata raporlama"
- "Telegram bildirim sistemi"
- "SQLite migration v2"

Sprint temaları (kötü örnekler):
- "Her şeyi iyileştir" → çok geniş
- "Tek satır düzeltme" → çok küçük

---

## References

- `task-granularity-calibration-skill/SKILL.md` — görev boyutu
- `parallel-task-identification-skill/SKILL.md` — süre kısaltma
- `multi-sprint-roadmap-design-skill/SKILL.md` — uzun vadeli plan
