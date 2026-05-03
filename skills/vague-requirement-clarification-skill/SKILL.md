---
name: vague-requirement-clarification
description: Planner AI için — kullanıcının belirsiz veya eksik isteklerini net gereksinimlere dönüştürmek amacıyla doğru soruları sormak ve netlik kazandırmak.
---

## Purpose

Kullanıcıdan gelen belirsiz istekleri uygulanabilir gereksinimlere dönüştürür.
Hangi sorunun sorulacağını, ne zaman sorulacağını ve cevap alındığında nasıl devam edileceğini belirler.
Aşırı soru sormaktan kaçınır; tek seferde en kritik belirsizliği giderir.

---

## When to Apply

- Kullanıcı isteği "bir şey yap", "düzelt", "güzel yap" gibi eylem içerip detay içermiyorsa
- Teknik seçim belirsizse (hangi kütüphane, hangi mimari)
- Kapsam belli değilse (ne kadar, hangi dosyalar, hangi flow)
- İki farklı yoruma açık cümle varsa

---

## Rules

- Tek seferde en fazla 2 soru sor. Kullanıcıyı form doldurmaya zorlamak yasak.
- Her soru "X mi Y mi" veya "X ne kadar olacak?" formatında, kapalı uçlu tercih edilir.
- Mimariyi etkileyen belirsizlikte mutlaka dur — küçük detaylarda makul varsayım yap, notu düş.
- Kullanıcı Türkçe yazıyorsa Türkçe sor.
- Cevap alınca `[PLANLAMA]` moduna geç, tekrar soru sorma.

---

## Guidelines

Belirsizliği tespit etme sırası:
1. **Kapsam**: Hangi dosyalar / modüller etkileniyor?
2. **Davranış**: Tam olarak ne yapmalı, ne yapmamalı?
3. **Kısıt**: Performans, güvenlik, uyumluluk kısıtı var mı?
4. **Bağlam**: Mevcut kodla entegre mi, sıfırdan mı?

Soru örüntüleri:
- "Bu sadece X modülü için mi, yoksa tüm sistem için mi?"
- "Mevcut `src/core/event_bus.py` üzerinde mi çalışacak, yoksa yeni bir dosya mı?"
- "Hata durumunda sessizce geçsin mi, yoksa kullanıcıya bildir mi?"

---

## Examples

```
Kullanıcı: "Logu düzelt"

YANLIŞ:
"Hangi log? Hangi dosya? Ne formatı? Nerede çıksın? Seviye ne olsun?"

DOĞRU:
[SOHBET] Hangi log kastediliyor — src/config/logging_config.py'deki format mı,
yoksa belirli bir modülün log seviyesi mi?
```

```
Kullanıcı: "Hızlandır"

DOĞRU:
[SOHBET] Hızlandırma hedefi: planner node'un LLM çağrısı mı,
yoksa SQLite read/write operasyonları mı?
```

---

## References

- `pm-mode-skill/SKILL.md` — mod geçiş kuralları
- `scope-boundary-detection-skill/SKILL.md` — kapsam belirleme
- `project-architecture-skill/SKILL.md` — hangi modülün ne yaptığı
