---
name: priority-ordering
description: Planner AI için — görevleri ve sprint'leri değer, bağımlılık ve risk faktörlerine göre sıralamak; önce en kritik işi yapmak.
---

## Purpose

Sınırlı kaynakla maksimum değer üretmek için görev sıralamasını belirler.
Kritik yol üzerindeki görevleri öne alır.
Yüksek riskli bağımlılıkları erken test eder.

---

## When to Apply

- Sprint sıralaması yapılırken
- Aynı anda başlayabilecek birden fazla görev varken
- Kullanıcı "nereden başlayalım?" diye sorduğunda
- Teknik borç vs. yeni özellik kararı verilirken

---

## Rules

- Kritik yol (başka işlerin bağımlı olduğu) görevler her zaman önce gelir.
- Yüksek belirsizlikli görevler erken yapılır — assumption'ları doğrulamak için.
- Interface/contract dosyaları implementasyondan önce yazılır.
- Teknik borç önceliği: sistemin çalışmasını engelliyorsa → yüksek; değilse → düşük.
- "Hoş ama kritik değil" özellikler en sona bırakılır.

---

## Guidelines

Öncelik matrisi:
```
YÜKSEK değer + DÜŞÜK efor  → hemen yap (quick win)
YÜKSEK değer + YÜKSEK efor → planlı sprint
DÜŞÜK değer + DÜŞÜK efor   → boş zamanda
DÜŞÜK değer + YÜKSEK efor  → yapma / ertele
```

Bu proje için sabit öncelik sırası:
1. `src/graph/state.py` değişiklikleri (her şey buna bağımlı)
2. Core servisler (`src/core/`)
3. Graph node'ları (`src/graph/nodes/`)
4. Storage/repository (`src/storage/`)
5. Interface'ler (`src/interfaces/`)
6. Scripts/test araçları

MoSCoW etiketleme:
- **M** (Must): Sprint bu olmadan tamamlanamaz
- **S** (Should): Önemli ama alternatif var
- **C** (Could): Güzel olur ama olmasa da olur
- **W** (Won't): Bu sprint değil

---

## Examples

```
3 görev, hangisi önce?

A: src/graph/state.py'e yeni alan ekle (M — diğerleri buna bağımlı)
B: src/graph/nodes/planner.py'i güncelle (S — A bitmeden başlanamaz)
C: Telegram bildirim formatı güncelle (C — bağımsız, ertelenebilir)

Sıra: A → B → C
```

---

## References

- `file-dependency-graph-design-skill/SKILL.md` — bağımlılık sırası
- `sprint-type-selection-skill/SKILL.md` — sprint türü
- `mvp-identification-skill/SKILL.md` — minimum gerekli set
