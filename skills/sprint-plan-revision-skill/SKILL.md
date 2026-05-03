---
name: sprint-plan-revision
description: Planner AI için — kullanıcı planı reddettiğinde geri bildirimi analiz ederek revize edilmiş plan oluşturmak; önceki hatayı tekrarlamamak.
---

## Purpose

Kullanıcı "hayır" dediğinde neden dediği anlaşılmalı.
Reddetme gerekçesi planı yönlendirir — körü körüne revizyon faydasız.
Revize plan, reddetme gerekçesini doğrudan ele almalı.

---

## When to Apply

- Kullanıcı planı reddedip gerekçe belirttiğinde
- `[ONAY-BEKLE]` sonrası ret mesajı alındığında
- Revize edilmiş plan hazırlanmadan önce

---

## Rules

- Ret gerekçesi her zaman okunur ve anlaşılır.
- Revize plan değişen kısımları açıkça belirtir.
- Değişmeyen kısımlar tekrar gösterilmez — sadece delta.
- Aynı plan 3 kez reddedilirse kapsam sorgulanır.

---

## Guidelines

Ret analiz kategorileri:
```
1. Kapsam çok geniş → sprint bölünmeli
2. Yanlış dosyalar hedeflenmiş → görevler revize edilmeli
3. Yaklaşım yanlış → farklı çözüm tasarlanmalı
4. Eksik görev → görev eklenmeli
5. Fazla görev → görev çıkarılmalı
```

```python
def analyze_rejection(rejection_reason: str) -> str:
    reason_lower = rejection_reason.lower()
    
    if any(kw in reason_lower for kw in ["fazla", "büyük", "çok"]):
        return "scope_too_large"
    elif any(kw in reason_lower for kw in ["yanlış", "hatalı", "değil"]):
        return "wrong_approach"
    elif any(kw in reason_lower for kw in ["eksik", "yok", "unutmuş"]):
        return "missing_task"
    else:
        return "unclear"
```

PM'in revizyon formatı:
```
[PLANLAMA] Geri bildiriminizi aldım.

Ret gerekçesi: "Telegram bildirimi de olmalı"

Revize plan (değişen kısımlar):
+ Görev 4 EKLENDİ: Telegram onay bildirimi
  - src/telegram/notifications.py
  - tests/test_telegram_notifications.py

Diğer görevler (1-3) değişmedi.

Bu planı onaylıyor musunuz?
```

---

## References

- `rejection-handling-skill/SKILL.md` — ret yönetimi
- `pm-mode-skill/SKILL.md` — PM modları
- `decision-log-maintenance-skill/SKILL.md` — karar kaydı
