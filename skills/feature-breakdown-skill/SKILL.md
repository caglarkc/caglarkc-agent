---
name: feature-breakdown
description: Planner AI için — büyük bir özellik isteğini birden fazla sprint'e bölmek; her sprint'in bağımsız, teslim edilebilir bir değer içermesini sağlamak.
---

## Purpose

"Tüm sistemi yaz" büyüklüğünde istek tek sprint'e sığmaz.
Her sprint bağımsız ve çalışan bir parça teslim etmeli.
Feature breakdown, büyük özelliği yönetilebilir parçalara böler.

---

## When to Apply

- Kullanıcı isteği birden fazla sprint gerektirecek büyüklükteyse
- Yeni modül veya entegrasyon istendiğinde
- "Her şeyi yap" tarzı istek alındığında

---

## Rules

- Her sprint bağımsız çalışmalı — önceki sprint olmadan teslim edilebilmeli.
- Sprint 1: temel altyapı (model, DB, temel servis).
- Sprint 2+: özellikler üzerine ekleme.
- Son sprint: test, dokümantasyon, polish.
- Breakdown önerisi kullanıcıya gösterilir ve onay alınır.

---

## Guidelines

Breakdown template:
```
Sprint 1 — Temel altyapı:
  - Pydantic modelleri
  - DB şeması ve repository
  - Temel servis sınıfı (CRUD)
  
Sprint 2 — Çekirdek işlevsellik:
  - Ana iş mantığı
  - LangGraph entegrasyonu
  - EventBus bağlantısı
  
Sprint 3 — Arayüz:
  - CLI komutları
  - Telegram entegrasyonu
  - Hata mesajları

Sprint 4 — Kalite:
  - Testler
  - Loglama
  - Konfigürasyon doğrulama
```

PM mesaj formatı:
```
[PLANLAMA] Bu istek 4 sprint gerektiriyor.

Breakdown önerim:

Sprint 1: Temel altyapı (models, DB, repository)
Sprint 2: LangGraph entegrasyonu (graph, node'lar)
Sprint 3: Arayüz (CLI + Telegram)
Sprint 4: Test ve polish

Hangi sprint'ten başlayalım?
```

---

## References

- `sprint-size-estimation-skill/SKILL.md` — sprint büyüklüğü
- `multi-sprint-roadmap-design-skill/SKILL.md` — roadmap
- `mvp-identification-skill/SKILL.md` — MVP tespiti
