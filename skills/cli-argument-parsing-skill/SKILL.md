---
name: cli-argument-parsing
description: Coder AI için — argparse veya Click ile CLI komutları ve argümanları tanımlamak; kullanıcı dostu hata mesajları vermek.
---

## Purpose

CLI kullanıcının agent'ı terminal üzerinden yönetmesini sağlar.
Argüman doğrulama erken hata yakalamayı sağlar.
`--help` otomatik üretilir — dokümantasyon yazmaya gerek kalmaz.

---

## When to Apply

- `src/interfaces/cli/commands.py` yazılırken
- Yeni CLI komutu eklenmesi gerektiğinde
- Argümanların tip ve kısıtlarla doğrulanması gerektiğinde

---

## Rules

- Click tercih edilir argparse'a göre (async desteği, dekoratör API).
- Zorunlu argüman: `@click.argument()`.
- Opsiyonel bayrak: `@click.option()` ile default değer.
- Async komut: `asyncio.run()` ile çalıştırılır.
- Hata: `click.echo(message, err=True)` + `sys.exit(1)`.

---

## Guidelines

```python
import click
import asyncio

@click.group()
def cli():
    """AI Development Agent CLI"""
    pass

@cli.command()
@click.argument("project_name")
@click.option("--description", "-d", default="", help="Proje açıklaması")
def create_project(project_name: str, description: str) -> None:
    """Yeni proje oluştur."""
    asyncio.run(_create_project(project_name, description))

@cli.command()
@click.argument("project_id")
@click.option("--limit", "-n", default=10, type=int, help="Sprint sayısı")
def list_sprints(project_id: str, limit: int) -> None:
    """Proje sprint'lerini listele."""
    asyncio.run(_list_sprints(project_id, limit))

@cli.command()
@click.argument("sprint_id")
@click.option("--reason", "-r", default="", help="Red gerekçesi")
def reject(sprint_id: str, reason: str) -> None:
    """Sprint planını reddet."""
    if not reason:
        click.echo("Hata: Red gerekçesi zorunlu (-r)", err=True)
        raise SystemExit(1)
    asyncio.run(_reject_sprint(sprint_id, reason))

# Entry point
if __name__ == "__main__":
    cli()
```

`pyproject.toml` script tanımı:
```toml
[project.scripts]
caglarkc = "src.interfaces.cli.commands:cli"
```

---

## References

- `daemon-ops-skill/SKILL.md` — daemon komutları
- `input-validation-patterns-skill/SKILL.md` — doğrulama
- `settings-validation-skill/SKILL.md` — config
