---
name: scope-creep-detection
description: Planner AI için — konuşma sırasında veya sprint ilerlerken kapsamın fark edilmeden genişlemesini tespit etmek ve durdurmak.
---

## Purpose

Scope creep'i erken tespit eder.
Planlama sırasında "bir de şunu yapalım" eklemeleri kontrolsüz büyümeye yol açar.
Mevcut sprint'e ekleme yerine yeni sprint olarak kayıt altına alınır.

---

## When to Apply

- Kullanıcı onay öncesinde yeni şeyler eklemeye başladığında
- Sprint ilerlerken "bir de X" şeklinde istekler geldiğinde
- Görev açıklaması orijinal isteğin dışına çıktığında

---

## Rules

- Mevcut sprint'e yeni dosya eklenirse → scope creep tespiti.
- "Bir de şunu ekle" → yeni backlog item, mevcut sprint'e girmez.
- Sprint başladıktan sonra (execution phase) yeni ekleme kabul edilmez.
- Küçük düzeltme (1 satır) izin verilir, yeni özellik izin verilmez.
- Tespit edildiğinde kullanıcıya açıkça bildirilir.

---

## Guidelines

Scope creep tespiti:
```
Sprint başlangıcı: planner.py retry ekle (2 dosya)

Kullanıcı execution sırasında: "Bir de Telegram'a bildirim ekle"
→ SCOPE CREEP TESPİT EDİLDİ

Yanıt:
[SOHBET] Mevcut sprint devam ediyor.
"Telegram bildirimi" için yeni görev açtım, bir sonraki sprint'e eklendi.
```

Büyüme sinyalleri:
```
"Bir de..." / "Aynı zamanda..." / "Bunu yaparken..."
"Basitçe X de ekle" (basitçe kelimesi tehlike işareti)
"Bu iş içinde de Y var zaten"
```

Backlog yönetimi:
```
Scope creep tespit edildiğinde:
1. Mevcut sprint değiştirilmez
2. Yeni item backlog'a eklenir
3. Kullanıcıya "Sprint N'de yapılacak" olarak bildirilir
4. Sprint bitince backlog item'ı bir sonraki sprint'e alınır
```

---

## References

- `scope-boundary-detection-skill/SKILL.md` — kapsam sınırı
- `sprint-size-estimation-skill/SKILL.md` — boyut tahmini
- `pm-mode-skill/SKILL.md` — mod geçiş kuralları
