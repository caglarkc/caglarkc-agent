---
name: config-schema-versioning
description: Coder AI için — konfigürasyon şemasının versiyonunu yönetmek; eski config dosyalarını yeni versiyona taşımak.
---

## Purpose

Konfigürasyon yapısı değişince eski config dosyaları çalışmaz.
Şema versiyonlama: her konfigürasyon değişikliği versiyonlanır.
Migration: eski versiyondan yeni versiyona otomatik dönüştürme.

---

## When to Apply

- Config yapısına yeni alan eklenirken
- Mevcut alan adı veya tipi değiştirilirken
- Config dosyası okunurken versiyon uyumsuzluğu tespit edildiğinde

---

## Rules

- Config: `schema_version` alanı içerir.
- Migration: mevcut versiyondan hedef versiyona adım adım geçiş.
- Geri dönüşümsüz migration: öncesi yedeklenir.
- Bilinmeyen versiyon: hata — kullanıcı uyarılır.

---

## Guidelines

```python
from typing import Callable

CURRENT_SCHEMA_VERSION = 3

MigrationFn = Callable[[dict], dict]

MIGRATIONS: dict[int, MigrationFn] = {
    1: lambda cfg: {**cfg, "log_level": cfg.pop("verbose", "INFO")},
    2: lambda cfg: {**cfg, "providers": {"llm": cfg.pop("llm_provider", "ollama")}},
    3: lambda cfg: {**cfg, "schema_version": 3},
}

def migrate_config(cfg: dict) -> dict:
    version = cfg.get("schema_version", 1)
    
    if version == CURRENT_SCHEMA_VERSION:
        return cfg
    if version > CURRENT_SCHEMA_VERSION:
        raise ValueError(f"Bilinmeyen config versiyonu: {version}")
    
    current = dict(cfg)
    for v in range(version, CURRENT_SCHEMA_VERSION):
        migrate_fn = MIGRATIONS.get(v + 1)
        if migrate_fn:
            current = migrate_fn(current)
    
    current["schema_version"] = CURRENT_SCHEMA_VERSION
    return current

def load_config_with_migration(path: str) -> dict:
    import json
    from pathlib import Path
    raw = json.loads(Path(path).read_text())
    return migrate_config(raw)

def save_config(cfg: dict, path: str) -> None:
    import json
    from pathlib import Path
    cfg["schema_version"] = CURRENT_SCHEMA_VERSION
    Path(path).write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
```

---

## References

- `settings-validation-skill/SKILL.md` — ayar doğrulama
- `env-file-setup-skill/SKILL.md` — ortam dosyası kurulumu
- `state-migration-skill/SKILL.md` — state taşıma
