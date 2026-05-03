---
name: rejection-handling
description: Planner AI için — kullanıcının planı reddetmesi durumunda gerekçeyi analiz etmek, planı revize etmek ve yeni onay döngüsünü başlatmak.
---

## Purpose

Ret sonrası planlamanın doğru şekilde devam etmesini sağlar.
Kullanıcının ret gerekçesini anlayarak planı revize eder.
Aynı planı tekrar sunmaktan kaçınır.

---

## When to Apply

- Kullanıcı `/reject` komutu verdiğinde
- `plan.rejected` event'i alındığında
- Onay timeout'a düştüğünde

---

## Rules

- Ret gerekçesi analiz edilir — boş ret ise gerekçe sorulur.
- Aynı plan tekrar sunulmaz — revize edilir veya sıfırlanır.
- Ret gerekçesi `revision_notes`'a kaydedilir.
- Ret sonrası `[PLANLAMA]` moduna geri dönülür.
- 3 ardışık ret → kullanıcıya "yeniden başlayalım mı?" sorusu.
- Timeout ret: bildirim gönderilir, session sonlandırılır.

---

## Guidelines

Ret işlem akışı:
```
1. Ret mesajını al: /reject <gerekçe>
2. Gerekçeyi analiz et:
   - "Çok büyük" → sprint bölünür
   - "Yanlış dosya" → kapsam düzeltilir
   - "Farklı yaklaşım" → alternatif plan üretilir
   - Boş ret → "[SOHBET] Hangi kısım uygun değildi?"
3. revision_notes'a kaydet
4. draft_plan'ı revize et
5. Yeni [ONAY-BEKLE] sun
```

Ret yanıtı formatı:
```
[PLANLAMA] Ret gerekçesi alındı: "<gerekçe>"

Revizyon:
• <neyi değiştirdim>
• <neden bu yaklaşım daha iyi>

[ONAY-BEKLE] — Revize plan:
...
```

Çok ret durumu:
```
3. ret sonrası:
[SOHBET] Bu planla 3 kez ret aldık. 
Tamamen farklı bir yaklaşım deneyelim mi, 
yoksa bu özelliği bekleteyim mi?
```

---

## References

- `approval-request-drafting-skill/SKILL.md` — onay formatı
- `multi-turn-context-preservation-skill/SKILL.md` — geçmiş bağlam
- `pm-mode-skill/SKILL.md` — mod geçişleri
