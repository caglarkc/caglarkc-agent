---
name: sprint-summary-generation
description: Planner AI için — sprint tamamlandığında ne yapıldığını, hangi dosyaların değiştiğini ve kullanıcının artık neler yapabileceğini özetleyen kısa bir rapor oluşturmak.
---

## Purpose

Sprint tamamlandığında kullanıcıya net bir "teslim özeti" sunar.
Kullanıcı neyin değiştiğini ve nasıl test edeceğini bilir.
Teknik ayrıntı değil, kullanıcı perspektifinden değer özeti.

---

## When to Apply

- `sprint.completed` event alındığında
- `[ONAY-BEKLE]`'den sonra onay alınıp sprint tamamlandığında
- Kullanıcı "ne bitti?" diye sorduğunda

---

## Rules

- Sprint özeti maksimum 10 satır.
- Dosya path'lerini tam yazmak yerine modül adı yeterli.
- "Artık yapabilirsiniz:" ile son kullanıcı değeri belirtilir.
- Başarısız dosyalar varsa açıkça belirtilir.
- Bir sonraki adım önerilir.

---

## Guidelines

Sprint özet formatı:
```
✅ Sprint {N} Tamamlandı

📦 Yapılan işler:
• Planner — LLM timeout retry (3 deneme, exponential backoff)
• Worker — Rate limit handling eklendi
• DB — worker_failure_log tablosu güncellendi

🎯 Artık:
• Geçici LLM hatalarında sistem sessizce yeniden dener
• Başarısız denemeler loglanır ve izlenebilir

⚠️ Dikkat:
• tests/test_retry.py manuel çalıştırılmalı: pytest tests/test_retry.py

➡️ Sıradaki: Telegram bildirim entegrasyonu (Sprint 4 planlandı)
```

Başarısız dosya içeren özet:
```
⚠️ Sprint {N} Kısmen Tamamlandı

✅ Başarılı (3/4):
• planner.py — retry eklendi
• worker.py — rate limit handling
• repository.py — failure log

❌ Başarısız (1/4):
• tests/test_retry.py — LLM mock hatası (3 denemede başarısız)

Manuel inceleme: /inspect tests/test_retry.py
```

---

## References

- `sprint-completion-validation-skill/SKILL.md` — tamamlanma kontrolü
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
- `pm-mode-skill/SKILL.md` — review modu
