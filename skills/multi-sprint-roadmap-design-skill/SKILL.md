---
name: multi-sprint-roadmap-design
description: Planner AI için — büyük bir projeyi veya özellik setini birden fazla sprint'e bölmek; hangi sprint'in hangisinden önce gelmesi gerektiğini belirlemek ve uzun vadeli yol haritası çıkarmak.
---

## Purpose

Büyük işleri yönetilebilir sprint serisine dönüştürür.
Her sprint'in bir sonrakinin zeminini hazırladığını garantiler.
Kullanıcıya "ne zaman ne görürüm?" sorusuna yanıt verir.

---

## When to Apply

- Kullanıcı isteği 5'ten fazla dosyayı etkiliyorsa
- Birden fazla bileşenin sırayla geliştirilmesi gerekiyorsa
- "Bu proje kaç sprint sürer?" sorusu sorulduğunda
- Yeni bir proje başlatılırken

---

## Rules

- Altyapı sprint'leri her zaman özellik sprint'lerinden önce gelir.
- Her sprint öncekine bağımlıysa sıra numarası ile belirtilir.
- Maksimum 8 sprint'lik yol haritası — daha uzunsa kilometre taşlarına böl.
- Her sprint'in bağımsız olarak tamamlanıp duraksanabilmesi gerekir.
- Sprint sırası değişirse bağımlılıklar yeniden değerlendirilir.

---

## Guidelines

Yol haritası şablonu:
```
PROJE: <proje adı>
TOPLAM SPRINT: <N>

Sprint 1 — Altyapı: <hedef>
  Dosyalar: <list>
  Bağımlılık: yok (ilk sprint)

Sprint 2 — Core Mantık: <hedef>
  Dosyalar: <list>
  Bağımlılık: Sprint 1

Sprint 3 — Entegrasyon: <hedef>
  Dosyalar: <list>
  Bağımlılık: Sprint 1, Sprint 2

...

KİLOMETRE TAŞI: Sprint 3 sonunda <kullanıcı değeri>
```

Bu proje için standart sprint sırası:
```
1. State/Contract güncellemeleri (eğer gerekiyorsa)
2. Core servis implementasyonu
3. LangGraph node güncellemesi
4. Storage/repository
5. Interface (CLI/Telegram)
6. Test ve validation
```

---

## Examples

```
Talep: "Projeye tam loglama ve monitoring sistemi ekle"

Yol haritası:
Sprint 1: Log formatı standardizasyonu (logging_config.py)
Sprint 2: Event bus'a monitoring event'leri (event_bus.py + contracts.py)
Sprint 3: SQLite'a log storage tablosu (repository.py)
Sprint 4: CLI log viewer komutu (cli/commands.py)
Sprint 5: Telegram monitoring digest (telegram/notifier.py)

Kilometre taşı: Sprint 3 sonunda tüm loglar DB'de sorgulanabilir
```

---

## References

- `sprint-size-estimation-skill/SKILL.md` — sprint boyutu
- `incremental-delivery-planning-skill/SKILL.md` — artımlı teslimat
- `priority-ordering-skill/SKILL.md` — sıralama
