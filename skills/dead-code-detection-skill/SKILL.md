---
name: dead-code-detection
description: Planner AI için — kullanılmayan import, fonksiyon, değişken, yorum satırı ve erişilemeyen kod bloklarını review sırasında tespit etmek ve temizletmek.
---

## Purpose

Kod tabanını temiz tutar.
Dead code okumayı zorlaştırır ve yanlış anlaşılmalara yol açar.
Kullanılmayan kod ileride yanlışlıkla çağrılabilir.

---

## When to Apply

- Her Coder AI kodu review'ında
- Refactoring sonrası
- Eski özellik kaldırıldığında

---

## Rules

- Kullanılmayan fonksiyon: hiçbir yerde çağrılmıyorsa kaldırılır.
- Kullanılmayan import: IDE veya grep ile doğrulanır.
- `pass` ile biten boş except bloğu: dead code işareti.
- Comment-out edilmiş kod: kaldırılır (git history var).
- `TODO: kaldır` veya `TODO: eski` yorumlu kod: hemen kaldırılır.
- Erişilemeyen kod (`return` sonrası satır): kaldırılır.

---

## Guidelines

Dead code tespit kalıpları:
```python
# 1. Kullanılmayan import
import os  # os. hiçbir yerde yok → kaldır

# 2. Unreachable code
def process():
    return result
    cleanup()  # return sonrası → dead code

# 3. Comment-out code
# old_function()  # bu satır ne zaman silinecek? → şimdi sil

# 4. Kullanılmayan fonksiyon
async def _old_helper():  # _ prefix + hiçbir yerde çağrılmıyor
    pass

# 5. Boş except
try:
    result = risky()
except Exception:
    pass  # sessiz başarısızlık = dead error handling

# 6. Kullanılmayan değişken
async def process(data: dict) -> str:
    unused_var = data.get("x")  # sonra kullanılmıyor
    return data.get("y", "")
```

Review sorusu: "Bu kod silinse bir şey bozulur mu?" → Hayır ise kaldır.

Güvenli kaldırma süreci:
1. Kodun kullanıldığı yer var mı? → `grep -r "function_name" src/`
2. Test ediyor mu? → Test dosyasını kontrol et
3. Yoksa → kaldır, commit mesajına not düş

---

## References

- `import-structure-review-skill/SKILL.md` — import temizliği
- `dry-principle-enforcement-skill/SKILL.md` — tekrar eden kod
- `function-length-review-skill/SKILL.md` — fonksiyon boyutu
