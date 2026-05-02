---
name: sprint-onboarding-guide
description: Planner AI için — yeni kullanıcıyı sisteme tanıştırmak; ilk sprint için adım adım rehber sunmak.
---

## Purpose

Yeni kullanıcı ne yapacağını bilmiyor — sıfırdan başlamak zor.
Onboarding rehberi: sistemi tanıtır, ilk sprint'i birlikte kurar.
5 adımda: proje tanımla → ilk hedef belirle → ayarları kontrol et → sprint başlat → sonucu gör.

---

## When to Apply

- Kullanıcı ilk kez sistemi kullandığında
- "Nasıl başlayacağım?" sorusu geldiğinde
- Yeni proje oluşturulduğunda

---

## Rules

- Onboarding: maksimum 5 adım.
- Her adım: ne yapılacak, neden, örnek.
- Teknik detay yok — yüksek seviye rehber.
- Tamamlanan adım işaretlenir ve atlanabilir.

---

## Guidelines

```python
from dataclasses import dataclass, field

@dataclass
class OnboardingStep:
    step_no:     int
    title:       str
    description: str
    example:     str
    completed:   bool = False

ONBOARDING_STEPS = [
    OnboardingStep(1, "Projeyi Tanımlayın",
        "Çalışacağınız projenin adını ve klasör yolunu belirtin.",
        "Proje adı: MyApp, Klasör: /home/user/myapp"),
    OnboardingStep(2, "LLM Sağlayıcısını Seçin",
        "Gemini, OpenRouter veya yerel Ollama kullanabilirsiniz.",
        ".env dosyasına GEMINI_API_KEY ekleyin"),
    OnboardingStep(3, "İlk Hedefi Belirleyin",
        "Basit bir özellik isteyin — sistemi test edin.",
        "Hedef: 'Merhaba Dünya' FastAPI endpoint'i ekle"),
    OnboardingStep(4, "Sprinti Başlatın",
        "Plan onaylandıktan sonra sistem otomatik çalışır.",
        "/sprint start komutu veya 'Başlat' düğmesi"),
    OnboardingStep(5, "Sonucu İnceleyin",
        "Sprint bitince üretilen dosyalar ve rapor görüntülenir.",
        "sprint tamamlandı mesajını bekleyin"),
]

def get_onboarding_progress(completed_steps: list[int]) -> str:
    lines = ["Başlangıç Rehberi:"]
    for step in ONBOARDING_STEPS:
        done = step.step_no in completed_steps
        mark = "✓" if done else "○"
        lines.append(f"  {mark} {step.step_no}. {step.title}")
        if not done:
            lines.append(f"     {step.description}")
            lines.append(f"     Örnek: {step.example}")
            break  # Sadece ilk tamamlanmamış adımı göster
    return "\n".join(lines)
```

---

## References

- `project-initialization-workflow-skill/SKILL.md` — proje başlatma
- `env-file-setup-skill/SKILL.md` — ortam dosyası
- `sprint-goal-validation-skill/SKILL.md` — hedef doğrulama
