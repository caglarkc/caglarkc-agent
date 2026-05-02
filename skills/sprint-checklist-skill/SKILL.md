---
name: sprint-checklist
description: Planner AI için — sprint başlatmadan önce tüm ön koşulların karşılandığını kontrol eden başlangıç kontrol listesi.
---

## Purpose

Sprint başlamadan önce eksik config, aktif sprint veya bozuk state tespit edilir.
Erken kontrol, yarı yolda durmaktan daha iyi.
"Her şey hazır mı?" sorusunu otomatik yanıtlar.

---

## When to Apply

- Kullanıcı sprint başlatmak istediğinde
- Planner node çalışmadan önce
- Daemon yeniden başladıktan sonra

---

## Rules

- Tüm kritik kontroller geçmeden sprint başlatılmaz.
- Uyarı seviyesindeki kontrol başlatmayı durdurmaz.
- Sonuç kullanıcıya sunulur: geçti / başarısız / uyarı.

---

## Guidelines

```python
from dataclasses import dataclass

@dataclass
class CheckItem:
    name: str
    critical: bool
    passed: bool = False
    message: str = ""

async def run_sprint_prechecks(
    project_id: str,
    settings: Settings,
    repo: ProjectRepository,
) -> list[CheckItem]:
    checks = []
    
    # 1. Proje mevcut mu?
    project = await repo.get_project(project_id)
    checks.append(CheckItem(
        name="Proje mevcut",
        critical=True,
        passed=project is not None,
        message="" if project else f"Proje bulunamadı: {project_id}",
    ))
    
    # 2. Aktif sprint var mı?
    active = await repo.get_active_sprint(project_id)
    checks.append(CheckItem(
        name="Aktif sprint yok",
        critical=True,
        passed=active is None,
        message=f"Mevcut aktif sprint: {active.sprint_id}" if active else "",
    ))
    
    # 3. LLM config var mı?
    checks.append(CheckItem(
        name="LLM konfigürasyonu",
        critical=True,
        passed=bool(settings.gemini_api_key or settings.ollama_base_url),
        message="Gemini veya Ollama konfigüre edilmeli",
    ))
    
    # 4. DB erişimi (uyarı)
    try:
        await repo.ping()
        db_ok = True
    except Exception:
        db_ok = False
    checks.append(CheckItem(
        name="DB erişimi", critical=True, passed=db_ok,
        message="" if db_ok else "DB bağlantısı kurulamadı",
    ))
    
    return checks

def all_critical_passed(checks: list[CheckItem]) -> bool:
    return all(c.passed for c in checks if c.critical)
```

---

## References

- `healthcheck-endpoint-skill/SKILL.md` — sağlık kontrolü
- `settings-validation-skill/SKILL.md` — config doğrulama
- `sprint-lifecycle-state-machine-skill/SKILL.md` — sprint durumu
