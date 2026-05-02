---
name: code-explanation
description: Planner AI için — üretilen kodu kullanıcıya anlaşılır şekilde açıklamak; ne yaptığını, neden bu yaklaşımın seçildiğini özetlemek.
---

## Purpose

Kullanıcı kodu anlamak isteyebilir — sadece "dosya yazıldı" yeterli değil.
Açıklama; mimari kararı, alternatifi ve kodun nasıl kullanılacağını kapsar.
Kısa ve odaklı açıklama, teknik olmayan kullanıcı için de anlaşılır.

---

## When to Apply

- Kullanıcı "bunu neden böyle yaptın?" diye sorduğunda
- Sprint tamamlandıktan sonra önemli kararlar özetlenirken
- Kod review'da bulgu açıklanırken

---

## Rules

- Açıklama: maksimum 5 cümle.
- Teknik jargon: parantez içi kısa açıklamayla.
- "Neden" önce — "ne" sonra.
- Alternatif yaklaşım: 1 cümleyle değinilir.
- Kod satırı tekrar edilmez — bağlam anlatılır.

---

## Guidelines

```python
def build_code_explanation_prompt(
    file_path: str,
    code_content: str,
    task_description: str,
) -> list:
    return [
        SystemMessage(content=(
            "Kısa ve anlaşılır kod açıklaması yaz. "
            "5 cümleyi geçme. Türkçe. "
            "Format: 'Bu kod [ne yapar]. [Neden bu yaklaşım]. "
            "[Nasıl kullanılır]. [Alternatif ne olurdu].'"
        )),
        HumanMessage(content=(
            f"Görev: {task_description}\n"
            f"Dosya: {file_path}\n\n"
            f"Kod:\n```python\n{code_content[:1000]}\n```"
        )),
    ]
```

PM açıklama formatı:
```
[SOHBET] provider_fallback.py hakkında:

Bu kod, LLM sağlayıcıları arasında otomatik geçişi yönetir.
Ollama önce denenir (ücretsiz, yerel); başarısız olursa OpenRouter'a geçilir.
Yeni sağlayıcı eklemek için listeye ekleme yeterli.
Alternatif yaklaşım: her denemede kullanıcıya seçim sunmak olabilirdi, 
ancak bu otomasyonu bozurdu.
```

---

## References

- `pm-mode-skill/SKILL.md` — PM modları
- `architecture-decision-record-skill/SKILL.md` — ADR
- `output-formatting-skill/SKILL.md` — çıktı formatı
