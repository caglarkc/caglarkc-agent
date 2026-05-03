---
name: parallel-task-identification
description: Planner AI için — bağımsız görevleri tespit ederek aynı anda birden fazla worker'a atanabilecek işleri belirlemek ve sprint süresini kısaltmak.
---

## Purpose

Sprint süresini kısaltmak için paralel çalıştırılabilecek görevleri belirler.
Dispatcher'ın aynı anda birden fazla worker'a iş atayabilmesini sağlar.
Gereksiz sıralı beklemeyi ortadan kaldırır.

---

## When to Apply

- Sprint'te 2'den fazla görev varken
- Dosya bağımlılık grafiği çizildikten sonra
- Worker atamaları yapılırken
- "Bu sprint ne kadar sürer?" sorusuna yanıt verirken

---

## Rules

- İki görev paralel çalışabilir sadece şu koşulda: aralarında import/veri/state bağımlılığı yoksa.
- Aynı dosyayı okuyan görevler paralel çalışabilir (okuma çakışmaz).
- Aynı dosyaya yazan görevler kesinlikle paralel çalışamaz.
- Test dosyaları test ettiği dosya bitmeden başlayamaz.

---

## Guidelines

Paralellik kontrol:
```
Görev A ve Görev B paralel çalışabilir mi?

1. A'nın hedef dosyası == B'nin hedef dosyası? → HAYIR (çakışır)
2. B, A'nın çıktısını import ediyor mu? → HAYIR (sıralı)
3. B, A'nın eklediği state alanını kullanıyor mu? → HAYIR (sıralı)
Hepsi HAYIR ise → EVET, paralel
```

Sprint paralel grupları yazım formatı:
```
PARALEL GRUP 1 (aynı anda başlar):
- worker_a: planner.py
- worker_b: repository.py
- worker_c: settings.py

PARALEL GRUP 2 (Grup 1 bittikten sonra başlar):
- worker_a: test_planner.py
- worker_b: test_repository.py
```

Sprint süresi tahmini:
- Sıralı: Tüm görevlerin toplamı
- Paralel: En uzun grubun süresi × grup sayısı

---

## Examples

```
6 görev için paralel analiz:

state.py → bağımsız (ilk)
contracts.py → bağımsız (ilk, state ile paralel)
planner.py → state + contracts bittikten sonra
dispatcher.py → state bittikten sonra (planner ile paralel)
test_planner.py → planner bittikten sonra
test_dispatcher.py → dispatcher bittikten sonra

Grup 1 (paralel): state.py + contracts.py
Grup 2 (paralel): planner.py + dispatcher.py
Grup 3 (paralel): test_planner.py + test_dispatcher.py

Toplam süre: 3 grup (6 yerine 3 bekleme)
```

---

## References

- `file-dependency-graph-design-skill/SKILL.md` — bağımlılık grafiği
- `worker-load-balancing-strategy-skill/SKILL.md` — worker atama
- `sequential-constraint-enforcement-skill/SKILL.md` — zorunlu sıralama
