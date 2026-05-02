---
name: sprint-project-template
description: Planner AI için — yaygın proje türleri için hazır sprint şablonları sunmak; FastAPI, CLI araç, LangGraph agent başlangıç konfigürasyonları.
---

## Purpose

Her yeni proje için sıfırdan sprint planlamak zaman alır.
Proje şablonu: "FastAPI servisi kur" → hazır görev listesi.
Şablon özelleştirilebilir — kullanıcı ihtiyacına göre uyarlanır.

---

## When to Apply

- Kullanıcı yeni proje başlatırken şablon istiyor
- Yaygın bir proje tipi (API, CLI, agent) kurulurken
- "Başlangıç projesi oluştur" isteğinde

---

## Rules

- Şablon: 5-10 görev, tahmini süre, dosya listesi.
- Özelleştirme: proje adı, Python sürümü, bağımlılıklar.
- Şablon seçimi: kullanıcı açıklamasından otomatik veya manuel.
- Çıktı: doğrudan sprint'e dönüştürülebilir.

---

## Guidelines

```python
PROJECT_TEMPLATES: dict[str, dict] = {
    "fastapi_service": {
        "name": "FastAPI Servisi",
        "description": "REST API servisi",
        "tasks": [
            {"id": "t1", "description": "pyproject.toml ve bağımlılıklar", "file": "pyproject.toml", "minutes": 10},
            {"id": "t2", "description": "FastAPI app oluştur", "file": "src/main.py", "minutes": 15},
            {"id": "t3", "description": "Pydantic modelleri", "file": "src/models.py", "minutes": 20},
            {"id": "t4", "description": "Router oluştur", "file": "src/routers/api.py", "minutes": 25},
            {"id": "t5", "description": "Konfigürasyon", "file": "src/config.py", "minutes": 10},
        ],
    },
    "cli_tool": {
        "name": "CLI Araç",
        "description": "Komut satırı aracı",
        "tasks": [
            {"id": "t1", "description": "pyproject.toml + Click setup", "file": "pyproject.toml", "minutes": 10},
            {"id": "t2", "description": "Ana CLI entry point", "file": "src/cli.py", "minutes": 20},
            {"id": "t3", "description": "Komut fonksiyonları", "file": "src/commands.py", "minutes": 25},
            {"id": "t4", "description": "Konfigürasyon yönetimi", "file": "src/config.py", "minutes": 15},
        ],
    },
    "langgraph_agent": {
        "name": "LangGraph Agent",
        "description": "Otonom agent",
        "tasks": [
            {"id": "t1", "description": "State tanımla", "file": "src/state.py", "minutes": 15},
            {"id": "t2", "description": "Node'ları yaz", "file": "src/nodes.py", "minutes": 30},
            {"id": "t3", "description": "Grafı kur", "file": "src/graph.py", "minutes": 20},
            {"id": "t4", "description": "Checkpoint konfigür", "file": "src/checkpointer.py", "minutes": 15},
            {"id": "t5", "description": "Ana çalıştırıcı", "file": "src/main.py", "minutes": 10},
        ],
    },
}

def apply_template(template_key: str, project_name: str) -> list[dict]:
    template = PROJECT_TEMPLATES.get(template_key)
    if not template:
        raise KeyError(f"Şablon bulunamadı: {template_key}")
    tasks = []
    for t in template["tasks"]:
        task = dict(t)
        task["file_path"] = t["file"].replace("src/", f"{project_name}/src/")
        task["estimated_minutes"] = t["minutes"]
        tasks.append(task)
    return tasks

def list_templates() -> str:
    lines = ["Mevcut Proje Şablonları:"]
    for key, tmpl in PROJECT_TEMPLATES.items():
        tasks = len(tmpl["tasks"])
        lines.append(f"  {key}: {tmpl['name']} ({tasks} görev)")
    return "\n".join(lines)
```

---

## References

- `sprint-template-library-skill/SKILL.md` — sprint şablon kütüphanesi
- `project-initialization-workflow-skill/SKILL.md` — proje başlatma
- `project-file-structure-skill/SKILL.md` — proje dosya yapısı
