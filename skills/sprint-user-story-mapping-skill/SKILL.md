---
name: sprint-user-story-mapping
description: Planner AI için — kullanıcı hikayelerini sprint'e dönüştürmek; "kullanıcı olarak X istiyorum" formatını görevlere çevirmek.
---

## Purpose

Teknik görev listesi kullanıcı değeriyle bağlantısını kaybeder.
User story mapping: her görev bir kullanıcı hikayesine dayanır.
"Neden bu dosyayı yazıyoruz?" sorusu her zaman yanıtlanabilir.

---

## When to Apply

- Kullanıcı özellik isteğini kullanıcı hikayesi olarak ifade ettiğinde
- Sprint planı kullanıcı değerine göre önceliklendirilirken
- Kabul kriterleri belirlenmesi gerektiğinde

---

## Rules

- Hikaye formatı: "Kullanıcı olarak [X] yapabilmek istiyorum, [sebep] için."
- Her hikayeye: kabul kriterleri (1-3 madde).
- Hikaye → görevler: 1 hikaye birden fazla göreve yol açabilir.
- Öncelik: iş değeri × risk skoru.

---

## Guidelines

```python
from dataclasses import dataclass, field

@dataclass
class UserStory:
    id:          str
    as_a:        str   # "kullanıcı" | "admin" | "developer"
    i_want:      str   # ne yapmak istiyor
    so_that:     str   # neden
    acceptance:  list[str] = field(default_factory=list)
    priority:    int   = 3  # 1=yüksek

STORY_TO_TASKS_PROMPT = """
Şu kullanıcı hikayesini Python görevlerine çevir.
Her görev: tek dosya, somut çıktı.

Hikaye: {story}
Kabul kriterleri: {acceptance}

JSON formatında döndür:
{{"tasks": [{{"id": "...", "description": "...", "file_path": "...", "acceptance_criterion": "..."}}]}}
"""

def format_user_story(story: UserStory) -> str:
    lines = [
        f"**{story.id}**: {story.as_a} olarak {story.i_want} istiyorum,",
        f"  çünkü {story.so_that}.",
    ]
    if story.acceptance:
        lines.append("  Kabul kriterleri:")
        for ac in story.acceptance:
            lines.append(f"    ✓ {ac}")
    return "\n".join(lines)

def prioritize_stories(stories: list[UserStory]) -> list[UserStory]:
    return sorted(stories, key=lambda s: s.priority)

def map_stories_to_sprint(stories: list[UserStory]) -> dict:
    return {
        "sprint_goal":    f"{len(stories)} kullanıcı hikayesi gerçeklendi",
        "user_stories":   [{"id": s.id, "description": s.i_want} for s in stories],
        "total_stories":  len(stories),
    }
```

---

## References

- `user-story-to-task-skill/SKILL.md` — hikaye → görev dönüşümü
- `sprint-goal-decomposition-skill/SKILL.md` — hedef parçalama
- `feature-breakdown-skill/SKILL.md` — özellik parçalama
