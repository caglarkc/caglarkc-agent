---
name: user-story-decomposition
description: Planner AI için — büyük kullanıcı isteklerini ve epikleri, Coder AI'ın uygulayabileceği küçük, bağımsız görevlere bölmek.
---

## Purpose

Büyük işleri Coder AI'ın tek seferde tamamlayabileceği parçalara ayırır.
Her parçanın net bir girdisi, çıktısı ve başarı kriteri vardır.
Bölünmüş görevler bağımsız paralel çalışmaya veya sıralı bağımlılığa göre düzenlenir.

---

## When to Apply

- Kullanıcı isteği 3'ten fazla dosyayı etkileyecekse
- Sprint'e girecek iş birden fazla katmanı kapsıyorsa
- Bir görev "ve ayrıca" içeriyorsa
- Tahmini efor tek worker için fazla büyükse

---

## Rules

- Her alt görev tek bir dosya veya en fazla 3 yakın ilişkili dosya kapsar.
- Her alt görev "Bitti" kriteri net olan bağımsız bir birimdir.
- Bağımlılık varsa sıra numarasıyla belirtilir: Görev 2, Görev 1 bitmeden başlamaz.
- "Refactor + feature" birlikte verilmez — ayrı görevler.
- Test görevi her zaman uygulama görevinden ayrı tutulur.

---

## Guidelines

Bölme adımları:
1. Tüm etkilenen dosyaları listele.
2. Her dosya veya dosya grubu için ayrı görev oluştur.
3. Bağımlılıkları belirle: hangi görev hangisini bekliyor?
4. Her göreve "Bitti kriteri" yaz.

Görev boyutu kontrolü:
- 1 worker, 1 dosya, 1 sprint → ideal
- 1 worker, 3 dosya, 1 sprint → kabul edilebilir
- 1 worker, 5+ dosya → tekrar böl

Örnek bölme:
```
Epic: "Planner node'a retry mantığı ekle ve log'a yaz"

Görev 1: src/graph/nodes/planner.py — retry dekoratörü entegre et
Görev 2: src/config/logging_config.py — planner retry log formatı
Görev 3: tests/test_planner_retry.py — retry senaryoları test et

Bağımlılık: Görev 2 → Görev 1'e bağımlı. Görev 3 → ikisine bağımlı.
```

---

## References

- `task-granularity-calibration-skill/SKILL.md` — görev boyutu
- `file-dependency-graph-design-skill/SKILL.md` — bağımlılık haritası
- `pm-mode-skill/SKILL.md` — görev prompt formatı
