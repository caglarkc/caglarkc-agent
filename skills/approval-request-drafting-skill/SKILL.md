---
name: approval-request-drafting
description: Planner AI için — kullanıcıya sunulacak onay isteğini net, özlü ve aksiyon alınabilir şekilde hazırlamak; teknik detayları kullanıcı diline çevirmek.
---

## Purpose

Kullanıcının onay isteklerini hızla anlayıp kararını vermesini sağlar.
Çok teknik veya çok uzun onay istekleri kullanıcıyı bunaltır.
Doğru formatlı onay isteği "evet/hayır" kararını kolaylaştırır.

---

## When to Apply

- Plan tamamlandıktan sonra, execution başlamadan önce
- `approval_request` oluşturulurken
- `[ONAY-BEKLE]` moduna geçilirken

---

## Rules

- Onay isteği maksimum 10 satır — özetle, tüm detayı verme.
- Hangi dosyaların değişeceği listele (tam path değil, modül adı).
- Kullanıcıya ne kazandıracağını söyle ("sonrasında X yapabileceksiniz").
- Teknik detay minimum — neden değil ne yapılacak.
- `/approve` ve `/reject` komutlarını hatırlat.
- Timeout: 15 dakika (ayarlanabilir).

---

## Guidelines

Onay isteği formatı:
```
[ONAY-BEKLE]

📋 PLAN: <sprint hedefi tek cümle>

Ne yapılacak:
• <dosya/modül 1> — <ne değişecek>
• <dosya/modül 2> — <ne değişecek>

Sonuç:
<Kullanıcı ne görecek/kazanacak>

Onaylamak için: /approve
Reddetmek için: /reject <gerekçe>

⏱️ 15 dakika içinde onay bekleniyor.
```

Kötü onay isteği (kaçınılacak):
```
[ONAY-BEKLE]
src/graph/nodes/planner.py'de async def planner_node fonksiyonuna
RetryDecorator implementasyonu eklenecek, exponential backoff ile
3 deneme yapılacak, her denemede 2^n saniye bekleme...
(teknik jargon → kullanıcı bunalır)
```

İyi onay isteği:
```
[ONAY-BEKLE]

📋 PLAN: LLM hatalarında sistem otomatik 3 kez yeniden dener

Ne yapılacak:
• Planner — Hata durumunda 3 deneme (2s/4s/8s bekleme)
• Worker — Aynı retry mantığı
• DB — Başarısız denemeler kaydedilir

Sonuç: Geçici LLM hatalarında kullanıcıya bildirim gitmez, sistem kendi çözer.
```

---

## References

- `pm-mode-skill/SKILL.md` — ONAY-BEKLE modu
- `sprint-goal-articulation-skill/SKILL.md` — sprint hedefi
- `rejection-handling-skill/SKILL.md` — ret durumu
