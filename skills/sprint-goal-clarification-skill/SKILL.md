---
name: sprint-goal-clarification
description: Planner AI için — belirsiz sprint hedefini netleştirmek için kullanıcıya odaklı sorular sormak ve yanıtları entegre etmek.
---

## Purpose

"Bir şeyler ekle" gibi belirsiz hedef farklı şekillerde yorumlanır.
Netleştirme: planlama öncesi hedefi somutlaştırır, yanlış anlamayı önler.
2-3 soru ile hedef: spesifik, ölçülebilir, uygulanabilir hâle gelir.

---

## When to Apply

- Kullanıcı hedefi soyut veya muğlak olduğunda
- Sprint planı oluşturmadan önce ön analiz gerektiğinde
- Teknik olmayan kullanıcı genel istek belirttiğinde

---

## Rules

- Sorular: maksimum 3, zorunlu cevap gerektiren.
- Soru türleri: kapsam, teknoloji tercihi, öncelik.
- Yanıtlar: state'e eklenir, planlama promptuna dahil edilir.
- Zaman sınırı: yanıt 5 dakika içinde gelmezse varsayılanlar kullanılır.

---

## Guidelines

```python
CLARIFICATION_QUESTIONS = {
    "scope": "Bu özellik hangi dosyaları veya modülleri etkiliyor?",
    "tech":  "Belirli bir kütüphane veya yaklaşım tercih ediyor musunuz?",
    "priority": "Hangi parça önce tamamlanmalı?",
}

async def clarify_sprint_goal(
    state: dict,
    llm,
) -> dict:
    goal = state.get("sprint_goal", "")

    analysis_prompt = f"""
Şu sprint hedefini değerlendir: "{goal}"
Hedef yeterince net mi? Eğer değilse, netleştirmek için 1-3 soru üret.
JSON: {{"clear": true/false, "questions": ["..."]}}
"""
    response = await llm.ainvoke([{"role": "user", "content": analysis_prompt}])

    import json, re
    match = re.search(r'\{.*\}', response.content, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group())
        if data.get("clear"):
            return {}
        return {
            "clarification_needed": True,
            "clarification_questions": data.get("questions", []),
        }
    except json.JSONDecodeError:
        return {}

def apply_clarifications(state: dict, answers: dict[str, str]) -> dict:
    goal   = state.get("sprint_goal", "")
    extras = "; ".join(f"{k}: {v}" for k, v in answers.items())
    return {
        "sprint_goal":         f"{goal} ({extras})",
        "clarification_answers": answers,
        "clarification_needed":  False,
    }
```

---

## References

- `intent-disambiguation-skill/SKILL.md` — niyet netleştirme
- `sprint-scope-negotiation-skill/SKILL.md` — kapsam müzakeresi
- `user-intent-clarification-skill/SKILL.md` — kullanıcı niyet
