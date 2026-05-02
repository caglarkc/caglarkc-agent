---
name: intent-disambiguation
description: Planner AI için — kullanıcı isteği belirsizse anlamlandırmak; farklı yorumları listeleyip doğruyu sormak.
---

## Purpose

"Kullanıcıyı düzelt" isteği ne demek? Profil mi, şifre mi, izinler mi?
Disambiguation: belirsiz istek çok yorumlu olduğunda seçenekler sunulur.
Yanlış yönde çalışmak yerine 1 soru sor, doğru ilerle.

---

## When to Apply

- Kullanıcı isteği 2+ farklı şekilde yorumlanabildiğinde
- Teknik olmayan kullanıcı jargon dışı ifade kullandığında
- Sprint planı oluşturulmadan önce hedef netleştirilirken

---

## Rules

- Disambiguate: en fazla 3 seçenek göster.
- Soru: kısa, net, teknik olmayan dil.
- Eğer %80+ bir yorum açıksa: o yorumu seç, not olarak ekle.
- Kullanıcı "hepsi" derse: ayrı sprint'lere böl.

---

## Guidelines

```python
DISAMBIGUATE_PROMPT = """
Kullanıcı isteği: "{request}"

Bu istek birden fazla şekilde yorumlanabilir mi?
Eğer evet, 2-3 somut yorum listele.
Eğer tek anlam varsa, "clear" döndür.

JSON formatında:
{{"ambiguous": true/false, "interpretations": ["...", "..."], "most_likely": "..."}}
"""

async def check_and_disambiguate(
    llm,
    user_request: str,
    conversation_context: str = "",
) -> dict:
    prompt = DISAMBIGUATE_PROMPT.format(request=user_request)
    if conversation_context:
        prompt = f"Önceki bağlam: {conversation_context}\n\n{prompt}"
    
    response = await llm.ainvoke([{"role": "user", "content": prompt}])
    
    import json, re
    match = re.search(r'\{.*\}', response.content, re.DOTALL)
    if not match:
        return {"ambiguous": False, "most_likely": user_request}
    
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {"ambiguous": False, "most_likely": user_request}

def build_clarification_message(analysis: dict) -> str | None:
    if not analysis.get("ambiguous"):
        return None
    options = analysis.get("interpretations", [])
    lines = ["İsteğinizi şu şekillerde anlayabiliyorum:"]
    for i, opt in enumerate(options, 1):
        lines.append(f"  {i}. {opt}")
    lines.append("\nHangisini yapmamı istersiniz?")
    return "\n".join(lines)
```

---

## References

- `user-intent-clarification-skill/SKILL.md` — kullanıcı niyet netleştirme
- `sprint-scope-negotiation-skill/SKILL.md` — kapsam müzakeresi
- `conversation-mode-routing-skill/SKILL.md` — konuşma yönlendirme
