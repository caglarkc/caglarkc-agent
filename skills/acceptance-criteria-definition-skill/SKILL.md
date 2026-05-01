---
name: acceptance-criteria-definition
description: Planner AI için — her sprint ve görev için "bitti" ne demektir sorusunu net kriterlerle yanıtlamak; onay öncesi kontrol listesi oluşturmak.
---

## Purpose

Bir görevin ne zaman tamamlanmış sayılacağını önceden tanımlar.
Subjektif "iyi görünüyor" değerlendirmelerinin önüne geçer.
Coder AI'ın teslim etmesi gereken minimum çıktıyı belirtir.

---

## When to Apply

- Her sprint başlamadan önce
- Coder AI'a görev verilmeden önce
- Review aşamasında "tamamlandı mı?" sorusu sorulurken
- Kullanıcıya onay sunulmadan önce

---

## Rules

- Kriterler ölçülebilir olmalı: "çalışıyor" yerine "X input verildiğinde Y output üretir".
- Her kriter test edilebilir olmalı.
- "Başarısız senaryo" da kriter olarak eklenir.
- Kriter listesi 3-7 madde arasında tutulur.
- Mimari kriterler (async, type hint, hata handling) her görevde zorunlu olarak eklenir.

---

## Guidelines

Kriter kategorileri:

**Fonksiyonel**
- Beklenen input → beklenen output
- Edge case → beklenen davranış
- Hata senaryosu → beklenen hata yanıtı

**Teknik (her görevde zorunlu)**
- Tüm fonksiyonlar async (IO içeriyorsa)
- Type hint tam
- try/except dış çağrılarda mevcut
- Yeni import `pyproject.toml`'da mevcut

**Entegrasyon**
- Event bus'a doğru event emit ediliyor
- State update doğru alanları döndürüyor
- Dosya yazma başarılı (ProjectManager üzerinden)

Kriter formatı:
```
KABUL KRİTERLERİ — <görev adı>

✓ <kriter 1>
✓ <kriter 2>
✓ <kriter 3>

BAŞARISIZLIK TANIMI:
✗ <bu durumda görev tamamlanmış sayılmaz>
```

---

## Examples

```
Görev: "planner.py'e draft_plan validation ekle"

KABUL KRİTERLERİ:
✓ draft_plan None ise state'e hata eklenir, sprint oluşturulmaz
✓ draft_plan eksik 'files' alanı içeriyorsa ValueError log'a yazılır
✓ Başarılı validation → sprint_id üretilir
✓ Fonksiyon async, dönüş tipi dict[str, Any]
✓ try/except Pydantic ValidationError sarıyor

BAŞARISIZLIK:
✗ None draft_plan crash'e yol açıyor → kabul edilmez
```

---

## References

- `pm-mode-skill/SKILL.md` — review kriterleri
- `sprint-goal-articulation-skill/SKILL.md` — sprint hedefi
- `test-strategy-planning-skill/SKILL.md` — test kapsamı
