---
name: healthcheck-endpoint
description: Coder AI için — daemon'ın sağlık durumunu raporlayan basit health check mekanizması; DB bağlantısı, LLM erişimi ve aktif sprint durumu.
---

## Purpose

Daemon çalışıyor mu? LLM erişilebilir mi? DB açık mı?
Health check bu soruları yanıtlar.
Monitoring, CI/CD ve manuel kontrol için.

---

## When to Apply

- `src/core/health.py` yazılırken
- CLI'ya `/health` veya `--check` komutu eklenirken
- Docker/process manager health probe yapılandırılırken

---

## Rules

- Health check: DB ping + LLM ping + aktif sprint sayısı.
- Sonuç: `healthy` / `degraded` / `unhealthy`.
- `degraded`: bazı bileşenler çalışmıyor ama devam edebilir.
- `unhealthy`: kritik bileşen çalışmıyor.
- Zaman aşımı: her ping 5 saniye.

---

## Guidelines

```python
from dataclasses import dataclass
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY   = "healthy"
    DEGRADED  = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    message: str = ""

@dataclass
class SystemHealth:
    overall: HealthStatus
    components: list[ComponentHealth]
    active_sprints: int = 0

async def check_db_health(db_path: str) -> ComponentHealth:
    try:
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute("SELECT 1")
        return ComponentHealth("database", HealthStatus.HEALTHY)
    except Exception as e:
        return ComponentHealth("database", HealthStatus.UNHEALTHY, str(e))

async def check_llm_health(llm: BaseChatModel) -> ComponentHealth:
    try:
        await asyncio.wait_for(
            llm.ainvoke([HumanMessage(content="ping")]),
            timeout=5.0
        )
        return ComponentHealth("llm", HealthStatus.HEALTHY)
    except asyncio.TimeoutError:
        return ComponentHealth("llm", HealthStatus.DEGRADED, "Timeout")
    except Exception as e:
        return ComponentHealth("llm", HealthStatus.UNHEALTHY, str(e))

async def get_system_health(
    db_path: str,
    llm: BaseChatModel,
    repo: ProjectRepository,
) -> SystemHealth:
    db_health, llm_health = await asyncio.gather(
        check_db_health(db_path),
        check_llm_health(llm),
    )
    components = [db_health, llm_health]
    
    if any(c.status == HealthStatus.UNHEALTHY for c in components):
        overall = HealthStatus.UNHEALTHY
    elif any(c.status == HealthStatus.DEGRADED for c in components):
        overall = HealthStatus.DEGRADED
    else:
        overall = HealthStatus.HEALTHY
    
    return SystemHealth(overall=overall, components=components)
```

---

## References

- `daemon-ops-skill/SKILL.md` — daemon yönetimi
- `settings-validation-skill/SKILL.md` — startup kontrol
- `logging-patterns-skill/SKILL.md` — durum loglama
