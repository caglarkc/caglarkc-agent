---
name: technical-debt-logging
description: Planner AI için — sprint sırasında ertelenen işleri, bilinen eksiklikleri ve iyileştirme fırsatlarını kayıt altına almak; teknik borç birikimini izlemek.
---

## Purpose

"Sonra düzeltiriz" denen şeyleri unutmamak için kayıt tutar.
Teknik borç görünür hale gelince önceliklendirmek kolaylaşır.
Sprint review sırasında ortaya çıkan eksiklikler sonraki sprint planlamaya girebilir.

---

## When to Apply

- Review sırasında "bunu şimdi yapmıyoruz ama not edelim" kararı verildiğinde
- Worker notu bıraktığında (BEKLENEN EKLEMELER, NOTLAR bölümü)
- Kullanıcı "şimdilik böyle kalsın" dediğinde
- Sprint kapsamı dışına çıkarılan iş tespit edildiğinde

---

## Rules

- Teknik borç `decisions` tablosuna `"technical_debt"` tipiyle kaydedilir.
- Her borç: ne, neden ertelendi, nasıl düzeltilir bilgisi içerir.
- Sprint başında backlog'dan teknik borç review edilir.
- Güvenlikle ilgili borç acil olarak işaretlenir.
- Borç birikmesi: 5'ten fazla açık borç varsa kullanıcıya bildirilir.

---

## Guidelines

Teknik borç formatı:
```python
await repo.create_decision(Decision(
    project_id=project_id,
    summary="[TEKNİK BORÇ] Worker retry sayacı kalıcı değil",
    rationale=(
        "Worker retry_count state'de tutuluyor, DB'ye yazılmıyor. "
        "Daemon restart olursa sayaç sıfırlanıyor. "
        "Düzeltme: WorkerFailureLog tablosunu retry takibi için kullan."
    ),
    decision_type="technical_debt"
))
```

PM'in borç takip mesajı:
```
[SOHBET] Bu sprint'te 2 teknik borç tespit edildi:

1. Worker retry sayacı kalıcı değil (orta öncelik)
2. Conversation history token limiti hesaplanmıyor (düşük öncelik)

Bunları bir sonraki sprint'e ekleyeyim mi?
```

Güvenlik borcunu acil işaretleme:
```python
Decision(
    summary="[TEKNİK BORÇ][ACİL] API key log'a düşüyor",
    rationale="llm_providers.py:45'te hata mesajı API key içeriyor. SecretStr maskeleme eksik.",
    decision_type="technical_debt"
)
# → Bir sonraki sprintin ilk görevi
```

---

## References

- `decision-log-maintenance-skill/SKILL.md` — karar kayıt
- `security-architecture-review-skill/SKILL.md` — güvenlik
- `priority-ordering-skill/SKILL.md` — önceliklendirme
