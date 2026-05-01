---
name: implicit-assumption-surfacing
description: Planner AI için — kullanıcının söylemediği ama varsaydığı şeyleri ortaya çıkarmak; gizli beklentileri ve kabul edilen varsayımları netleştirmek.
---

## Purpose

Söylenmeyip varsayılan şeyler sprint sırasında sürpriz olarak ortaya çıkar.
"Tabii ki X de olacak" varsayımı cevapsız bırakılırsa sprint yanlış tamamlanır.
Varsayımlar önceden netleştirilirse sürpriz değişiklik olmaz.

---

## When to Apply

- Kullanıcı isteği "basit" veya "az" gibi göründüğünde
- İsteğin birden fazla yorumu mümkün olduğunda
- Mevcut sistemle entegrasyon ima edildiğinde
- "Tabii ki", "zaten", "otomatik olarak" gibi ifadeler geçtiğinde

---

## Rules

- Varsayım tespit edilirse doğrulama sorusu sorulur.
- Makul varsayım yapılabilecekse: varsayım not edilir, kullanıcıya bildirilir, soru sorulmaz.
- "Tabii ki olur" diye geçilen şey sprint sonunda beklenti boşluğu yaratabilir.
- Mimariyi etkileyen varsayım mutlaka netleştirilir.

---

## Guidelines

Yaygın gizli varsayımlar:

**Telegram**: "Eklediğimde otomatik bildirim gider" — Telegram aktif mi? token var mı?
**CLI**: "Her zaman açık olacak" — daemon modunda mı?
**DB**: "Eski veriler korunur" — migration gerekiyor mu?
**Auth**: "Kullanıcı zaten giriş yapmış" — kimlik doğrulama mekanizması var mı?
**Format**: "JSON çıktı üretir" — hangi format? şema nedir?

Varsayım not formatı:
```
[SOHBET] Planı oluşturmadan önce bir varsayımı doğrulayalım:

"Telegram bildirimi" derken mevcut bot token konfigürasyonunu 
kullanan bir bildirim mi? Yoksa yeni bir bot mu?

(varsayımım: mevcut bot, direkt devam edebilirim — doğru mu?)
```

Makul varsayım notu:
```
[PLANLAMA] 
Not: Telegram bildirimi için mevcut TELEGRAM_BOT_TOKEN'ı kullanacağımı 
varsayıyorum. Farklı bir bot istiyorsanız belirtin.
```

---

## References

- `vague-requirement-clarification-skill/SKILL.md` — belirsizlik netleştirme
- `scope-boundary-detection-skill/SKILL.md` — kapsam sınırı
- `requirement-conflict-detection-skill/SKILL.md` — çakışma tespiti
