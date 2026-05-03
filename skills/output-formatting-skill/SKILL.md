---
name: output-formatting
description: Planner AI için — kullanıcıya sunulan mesajları tutarlı, okunabilir formatta yazmak; PM mod etiketleri ve yapısal düzeni korumak.
---

## Purpose

Tutarsız format kullanıcının hangi bilginin ne anlama geldiğini anlamasını zorlaştırır.
PM mod etiketleri (`[SOHBET]`, `[PLANLAMA]` vb.) mesajın türünü belirtir.
İyi biçimlendirilmiş mesaj güven verir.

---

## When to Apply

- Her PM mesajı yazılırken
- Sprint planı, onay isteği, durum raporu sunulurken
- Hata veya uyarı mesajı iletilirken

---

## Rules

- Her mesaj uygun mod etiketiyle başlar.
- Liste öğeleri: markdown bullet (`-`) veya numaralı.
- Dosya yolları: `backtick` ile.
- Uzun mesaj: bölümlere ayrılır, başlık satırı düz metin.
- Emoji yok — sadece ASCII karakterler.

---

## Guidelines

Mod etiket rehberi:
```
[SOHBET]        — Genel konuşma, soru, bilgi
[PLANLAMA]      — Sprint planı, görev listesi
[GÖREV]         — Teknik detay, implementasyon notu
[REVIEW]        — Kod inceleme sonucu
[ONAY-BEKLE]    — Kullanıcıdan onay isteme
```

Sprint planı formatı:
```
[PLANLAMA] Sprint 4 — Telegram entegrasyonu

Hedef: Onay/ret akışını Telegram üzerinden yönetmek

Görevler:
1. Handler'lar — src/interfaces/telegram/handlers.py
2. Komut kaydı — /approve, /reject, /status
3. Testler — tests/test_telegram_handlers.py

Etkilenen dosyalar: 3 yeni, 1 değişiklik

Bu planı onaylıyor musunuz? (evet/hayır/değiştir)
```

Hata formatı:
```
[SOHBET] Sprint sırasında sorun oluştu:

Hata: src/graph/nodes/worker.py yazılamadı
Sebep: Dizin mevcut değil (src/graph/nodes/)

Çözüm: Dizin oluşturulacak ve yeniden denenecek.
Devam etmemi ister misiniz?
```

---

## References

- `pm-mode-skill/SKILL.md` — PM modları
- `progress-report-generation-skill/SKILL.md` — rapor
- `sprint-completion-celebration-skill/SKILL.md` — tamamlanma
