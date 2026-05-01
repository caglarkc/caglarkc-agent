---
name: technical-feasibility-check
description: Planner AI için — kullanıcının istediği şeyin mevcut mimari, bağımlılıklar ve kısıtlar çerçevesinde yapılabilir olup olmadığını değerlendirmek.
---

## Purpose

Sprint planlamaya başlamadan önce teknik engelleri tespit eder.
Yapılamayacak veya mevcut mimariye uymayan talepleri erken filtreler.
Uygulanabilir alternatifler önerir.

---

## When to Apply

- Kullanıcı yeni bir özellik talep ettiğinde
- Mevcut koda büyük değişiklik planlanırken
- Üçüncü taraf servis veya kütüphane entegrasyonu istendiğinde
- Performans veya ölçek gereksinimleri belirtildiğinde

---

## Rules

- Kütüphane kontrolü: `pyproject.toml`'da olmayan paket gerekiyorsa kullanıcıya bildirilir, otomatik eklenmez.
- Async uyumluluk: Yeni bileşen mevcut async event loop ile çalışabilir mi?
- LangGraph state uyumu: Yeni state alanı gerektiriyor mu? Gerektiriyorsa `state.py` değişikliği ayrı sprint.
- SQLite kısıtı: Concurrent write yasak, her operasyon sıralı async ile yapılır.
- Ollama bağımlılığı: Local model gerektiren özellikler Ollama'nın ayakta olmasına bağlıdır.

---

## Guidelines

Fizibilite kontrol listesi:
1. **Bağımlılık**: Gerekli kütüphane `pyproject.toml`'da var mı?
2. **Async uyum**: Blocking call içeriyor mu?
3. **State değişikliği**: `OrchestratorState` yeni alan gerektiriyor mu?
4. **Dosya erişimi**: Worker kendi alanı dışına çıkıyor mu?
5. **API anahtarı**: Yeni dış servis için `.env` değişkeni gerekiyor mu?
6. **Test edilebilirlik**: Mock/stub yapılabilir mi?

Sonuç formatı:
```
FİZİBİLİTE SONUCU: UYGULANABILIR / KISITLI / UYGULANAMAZ

Engeller:
- <varsa>

Gereksinimler:
- <yeni paket / env key / state alanı>

Öneri:
- <alternatif yaklaşım>
```

---

## Examples

```
Talep: "WebSocket ile gerçek zamanlı güncelleme ekle"

Fizibilite:
- websockets paketi pyproject.toml'da yok → eklenmeli
- Mevcut Textual TUI websocket destekliyor mu? → kontrol gerekiyor
- LangGraph event bus üzerinden emit → UYGULANABILIR (mevcut altyapı yeterli)

Sonuç: KISITLI — websockets paketi eklenmeli, Textual uyumu doğrulanmalı
```

---

## References

- `project-architecture-skill/SKILL.md` — mevcut mimari kısıtlar
- `python-async-patterns-skill/SKILL.md` — async uyumluluk
- `non-functional-requirement-extraction-skill/SKILL.md` — kısıt analizi
