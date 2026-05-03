---
name: architecture-decision-record
description: Planner AI için — önemli mimari kararları ADR (Architecture Decision Record) formatında kaydetmek; neden bu yaklaşım seçildi, alternatifleri nelerdi.
---

## Purpose

Büyük mimari kararların gerekçesini gelecek için saklar.
"Neden LangGraph seçtik?" veya "Neden SQLite?" gibi soruları yanıtlar.
Yeni geliştirici veya ilerideki sprint'ler için bağlam sağlar.

---

## When to Apply

- Yeni teknoloji veya kütüphane seçildiğinde
- Mimari pattern değiştirildiğinde (event-driven, HITL, checkpoint)
- İki yaklaşım arasında önemli bir seçim yapıldığında
- Kullanıcı "neden böyle yaptık?" diye sorduğunda

---

## Rules

- ADR: `decisions` tablosuna `"architecture"` tipiyle kaydedilir.
- Format: Durum, Bağlam, Karar, Sonuç, Alternatifler.
- ADR geri alınamaz — yeni ADR eklenebilir (supersedes).
- Kısa ADR tercih edilir: 5-10 cümle yeterli.

---

## Guidelines

ADR formatı:
```python
ADR_TEMPLATE = """
DURUM: {status}  # Önerilen / Kabul edildi / Reddedildi / Geçersiz

BAĞLAM:
{context}

KARAR:
{decision}

SONUÇ:
{consequence}

ALTERNATİFLER DEĞERLENDİRİLDİ:
{alternatives}
"""

# Örnek ADR
await repo.create_decision(Decision(
    project_id=project_id,
    summary="[ADR-001] LangGraph checkpoint için AsyncSqliteSaver seçildi",
    rationale=(
        "DURUM: Kabul edildi\n"
        "BAĞLAM: Graph state'inin daemon restart'larına karşı dayanıklı olması gerekiyor.\n"
        "KARAR: AsyncSqliteSaver kullanıldı — aiosqlite tabanlı, kurulum gerektirmiyor.\n"
        "SONUÇ: Checkpoint DB ayrı dosyada (graph_checkpoint.db), "
        "production deploy için bakım gerektirmez.\n"
        "ALTERNATİFLER: PostgreSQL (fazla karmaşık), Redis (ek bağımlılık), "
        "MemorySaver (restart'a dayanıksız)."
    ),
    decision_type="architecture"
))
```

PM'in ADR önerme formatı:
```
[PLANLAMA] Mimari karar önerisi:

Öneri: EventBus için pub/sub pattern (mevcut yaklaşım korunuyor)
Alternatif: Direkt fonksiyon çağrısı (daha basit ama coupling artıyor)

Tercih: EventBus — interface bağımsızlığı sağlıyor.
ADR kaydedildi: ADR-005
```

---

## References

- `decision-log-maintenance-skill/SKILL.md` — karar kayıt
- `module-boundary-validation-skill/SKILL.md` — mimari sınırlar
- `sprint-summary-generation-skill/SKILL.md` — sprint özeti
