---
name: sprint-configuration-profile
description: Planner AI için — farklı kullanım senaryoları için hazır sprint konfigürasyon profilleri tanımlamak (hızlı, kapsamlı, güvenli).
---

## Purpose

Her sprint aynı ayarlarla çalışmak verimsiz.
Profiller: "hızlı prototip" vs "üretim kalitesi" farklı konfigürasyonlar.
Kullanıcı profil seçer, sistem parametreleri otomatik ayarlar.

---

## When to Apply

- Sprint başlatılırken konfigürasyon seçimi gerektiğinde
- Kullanıcı "hızlı bir şey dene" veya "titizlikle yap" dediğinde
- CI/CD'de ortama göre farklı ayar gerektiğinde

---

## Rules

- Profil: isim + açıklama + parametre seti.
- Parametreler: max_workers, timeout, quality_checks, retry_limit.
- Kullanıcı seçmezse: `balanced` profil varsayılan.
- Profil override edilebilir — bireysel parametre geçersiz kılma.

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class SprintProfile:
    name:             str
    description:      str
    max_workers:      int
    llm_timeout:      float
    max_retries:      int
    quality_checks:   bool
    lint_enabled:     bool
    test_enabled:     bool
    sprint_minutes:   int

PROFILES: dict[str, SprintProfile] = {
    "fast": SprintProfile(
        name="Hızlı Prototip",
        description="Kalite kontrolü az, hız öncelikli",
        max_workers=3,
        llm_timeout=30.0,
        max_retries=1,
        quality_checks=False,
        lint_enabled=False,
        test_enabled=False,
        sprint_minutes=30,
    ),
    "balanced": SprintProfile(
        name="Dengeli",
        description="Hız ve kalite dengesi (varsayılan)",
        max_workers=3,
        llm_timeout=60.0,
        max_retries=2,
        quality_checks=True,
        lint_enabled=True,
        test_enabled=False,
        sprint_minutes=60,
    ),
    "quality": SprintProfile(
        name="Üretim Kalitesi",
        description="Kapsamlı kontroller, yüksek güvenilirlik",
        max_workers=2,
        llm_timeout=90.0,
        max_retries=3,
        quality_checks=True,
        lint_enabled=True,
        test_enabled=True,
        sprint_minutes=120,
    ),
}

def select_profile(name: str = "balanced", **overrides) -> SprintProfile:
    profile = PROFILES.get(name, PROFILES["balanced"])
    if overrides:
        import dataclasses
        return dataclasses.replace(profile, **overrides)
    return profile

def list_profiles() -> str:
    lines = ["Mevcut Profiller:"]
    for key, p in PROFILES.items():
        lines.append(f"  {key}: {p.name} — {p.description}")
    return "\n".join(lines)
```

---

## References

- `settings-validation-skill/SKILL.md` — ayar doğrulama
- `sprint-resource-limits-skill/SKILL.md` — kaynak sınırları
- `config-schema-versioning-skill/SKILL.md` — config versiyonlama
