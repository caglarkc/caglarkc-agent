---
name: sprint-team-collaboration
description: Planner AI için — birden fazla kullanıcının aynı proje üzerinde çalıştığı senaryolarda sprint koordinasyonu.
---

## Purpose

Tek kullanıcı varsayımıyla kurulu sistem multi-user'da çakışır.
Ekip işbirliği: kim ne üzerinde çalışıyor, çakışma var mı?
Lock mekanizması: aynı dosyayı iki kullanıcı aynı anda düzenleyemez.

---

## When to Apply

- Birden fazla kullanıcı aynı projeyi kullandığında
- Paralel sprint başlatma isteği geldiğinde
- Dosya çakışması tespit edildiğinde

---

## Rules

- Proje başına bir aktif sprint sahibi (lock).
- Kilit: 30 dakika — sonra otomatik serbest kalır.
- Başka kullanıcı sprint başlatmak isterse: uyarı ve bekle.
- Sadece kilit sahibi sprint'i onaylayabilir veya iptal edebilir.

---

## Guidelines

```python
from datetime import datetime, timedelta

SPRINT_LOCK_DURATION_MINUTES = 30

def acquire_project_lock(
    state: dict,
    user_id: str,
    project_id: str,
) -> tuple[bool, str]:
    locks = state.get("project_locks", {})
    lock  = locks.get(project_id)
    
    if lock:
        locked_by  = lock["user_id"]
        locked_at  = datetime.fromisoformat(lock["locked_at"])
        expired = (datetime.utcnow() - locked_at).total_seconds() / 60 > SPRINT_LOCK_DURATION_MINUTES
        
        if not expired and locked_by != user_id:
            remaining = SPRINT_LOCK_DURATION_MINUTES - (datetime.utcnow() - locked_at).total_seconds() / 60
            return False, f"Proje {locked_by} tarafından kilitli ({remaining:.0f} dk kaldı)"
    
    locks[project_id] = {
        "user_id":   user_id,
        "locked_at": datetime.utcnow().isoformat(),
    }
    return True, ""

def release_project_lock(state: dict, project_id: str, user_id: str) -> dict:
    locks = dict(state.get("project_locks", {}))
    lock  = locks.get(project_id)
    
    if lock and lock["user_id"] == user_id:
        del locks[project_id]
    
    return {"project_locks": locks}

def get_active_sprint_owner(state: dict, project_id: str) -> str | None:
    lock = state.get("project_locks", {}).get(project_id)
    return lock["user_id"] if lock else None
```

---

## References

- `multi-project-support-skill/SKILL.md` — çoklu proje desteği
- `async-lock-usage-skill/SKILL.md` — async kilit kullanımı
- `sprint-conflict-resolution-skill/SKILL.md` — çakışma çözümü
