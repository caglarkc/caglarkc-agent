---
name: multi-turn-context-preservation
description: Planner AI için — çok turlu konuşmalarda bağlamı korumak; kullanıcının önceki mesajlarını, alınan kararları ve mevcut plan durumunu doğru takip etmek.
---

## Purpose

Konuşmanın geçmişini eksiksiz aktararak planlama kalitesini artırır.
Kullanıcının daha önce söylediğini tekrar sordurtmaktan kaçınır.
Manager planning service'in conversation_history alanını doğru yönetir.

---

## When to Apply

- Kullanıcı aynı proje için ikinci veya daha sonraki mesajı gönderdiğinde
- Mevcut draft_plan güncellenirken
- Onay/ret sonrası planlama devam ederken
- "Az önce söylediğim gibi..." veya "Bunu değiştir" gibi referanslı isteklerde

---

## Rules

- `conversation_history` her turda güncellenir: `[{"role": "user/manager", "content": "..."}]`
- Geçmiş maksimum 20 tur saklanır — daha fazlası ilk turlar silinerek kırpılır.
- `draft_plan` mevcut plana ek yapılır, sıfırdan başlamaz (revizyon modunda).
- Onay beklenirken `[ONAY-BEKLE]` modunda yeni planlama yapılmaz.
- Kullanıcı planı reddederse neden reddettiği geçmişe kaydedilir.

---

## Guidelines

Bağlam yönetimi:
```python
# conversation_history güncelleme
state["conversation_history"] = (
    state.get("conversation_history", []) + [
        {"role": "user", "content": user_message},
        {"role": "manager", "content": manager_reply}
    ]
)[-40:]  # son 20 çift = 40 entry, öncesi kırpılır
```

Revizyon vs. sıfırlama:
```
Kullanıcı: "Planner'a retry ekle"
→ Mevcut draft_plan'a ekleme yapılır

Kullanıcı: "Baştan planla, farklı bir yaklaşım dene"
→ draft_plan temizlenir, yeni plan oluşturulur
```

Önemli kararları koruma:
```
Karar: "Telegram yerine CLI kullanılacak" (Sprint 2'de alındı)
→ conversation_history'de referans olarak kalır
→ Sprint 5'te "Telegram ekle" istenirse önceki kararla çelişme tespit edilir
```

---

## References

- `pm-mode-skill/SKILL.md` — mod yönetimi
- `approval-request-drafting-skill/SKILL.md` — onay süreci
- `conversation-history-trimming-skill/SKILL.md` — geçmiş yönetimi
