---
name: mode-transition-detection
description: Planner AI için — pm-mode'un 5 modu arasında (SOHBET, PLANLAMA, GÖREV, REVIEW, ONAY-BEKLE) doğru geçiş zamanını tespit etmek.
---

## Purpose

PM modları arasındaki geçişleri otomatik ve doğru şekilde yönetir.
Yanlış modda kalmak: onay beklerken planlama yapmak, review yapmadan onay sunmak.
Her mod geçişi net bir tetikleyici koşula bağlıdır.

---

## When to Apply

- Her kullanıcı mesajı alındığında
- Sprint lifecycle'ının her adımında
- Node çıktısı geldiğinde

---

## Rules

- `[SOHBET]`: Soru/cevap, netleştirme. Execution intent yok.
- `[PLANLAMA]`: Execution intent tespit edildi, plan oluşturuluyor.
- `[GÖREV]`: Plan onaylandı, Coder AI'a görev prompt'u yazılıyor.
- `[REVIEW]`: Coder AI çıktısı geldi, inceleniyor.
- `[ONAY-BEKLE]`: Review tamamlandı, kullanıcı onayı bekleniyor.

---

## Guidelines

Geçiş tetikleyicileri:
```
Herhangi mod → [SOHBET]:
  - Kullanıcı soru sordu
  - Belirsizlik tespit edildi
  - Küçük açıklama gerekiyor

[SOHBET] → [PLANLAMA]:
  - Execution intent tespit edildi
  - Tüm bilgiler yeterli

[PLANLAMA] → [GÖREV]:
  - draft_plan tamamlandı
  - Plan onaylandı (veya otomatik onay aktif)

[GÖREV] → [REVIEW]:
  - Coder AI çıktısı alındı
  - Worker queue'daki görev tamamlandı

[REVIEW] → [ONAY-BEKLE]:
  - Review pozitif — ONAY verildi
  - Kullanıcıya sunulmaya hazır

[REVIEW] → [GÖREV]:
  - Review negatif — REVIZE
  - Yeni görev prompt'u üret

[ONAY-BEKLE] → [PLANLAMA]:
  - Kullanıcı reddetti → yeniden planla

[ONAY-BEKLE] → [GÖREV]:
  - Kullanıcı onayladı → bir sonraki sprint
```

Mod etiketi zorunlu:
```
Her yanıt ilgili modun etiketiyle başlar:
[SOHBET] Hangi dosyayı değiştirmemeli?
[PLANLAMA] 3 görev belirledim...
[GÖREV] GÖREV: planner.py retry ekle...
[REVIEW] ONAY: tüm kriterler geçti
[ONAY-BEKLE] Planı onaylar mısınız?
```

---

## References

- `pm-mode-skill/SKILL.md` — mod tanımları
- `execution-intent-detection-skill/SKILL.md` — intent tespiti
- `approval-request-drafting-skill/SKILL.md` — onay formatı
