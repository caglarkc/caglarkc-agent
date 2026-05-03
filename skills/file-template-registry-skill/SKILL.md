---
name: file-template-registry
description: Coder AI için — sık kullanılan dosya şablonlarını kayıt altında tutmak; yeni dosyaları şablondan oluşturmak.
---

## Purpose

Her seferinde sıfırdan dosya yapısı üretmek tutarsızlığa yol açar.
Şablon kayıt defteri: FastAPI router, LangGraph node, test dosyası gibi kalıpları saklar.
Yeni dosya isteklerinde şablon seçilir, placeholder'lar doldurulur.

---

## When to Apply

- Yeni Python modülü oluşturulurken
- LangGraph node eklenmesi istendiğinde
- Test dosyası iskeleti hazırlanırken

---

## Rules

- Şablonlar string formatı kullanır (`{class_name}`, `{module_name}` vb.).
- Her şablonun kısa açıklaması ve placeholder listesi belgelidir.
- Şablon bulunamazsa: boş iskelet + temel import'lar.
- Üretilen dosya linter'dan geçirilir.

---

## Guidelines

```python
from string import Template

FILE_TEMPLATES: dict[str, str] = {
    "langgraph_node": '''from typing import Any
from ${state_type} import ${state_class}

async def ${node_name}(state: ${state_class}) -> dict[str, Any]:
    """${description}"""
    # TODO: implement
    return {}
''',
    "pytest_module": '''import pytest
from ${module_path} import ${class_or_func}

class Test${TestClass}:
    def test_${test_name}(self):
        # Arrange
        # Act
        # Assert
        pass
''',
    "fastapi_router": '''from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/${prefix}", tags=["${tag}"])

class ${RequestModel}(BaseModel):
    pass

@router.post("/")
async def ${endpoint_name}(body: ${RequestModel}):
    return {}
''',
}

def render_template(template_key: str, **kwargs) -> str:
    template_str = FILE_TEMPLATES.get(template_key)
    if not template_str:
        raise KeyError(f"Şablon bulunamadı: {template_key}")
    return Template(template_str).substitute(**kwargs)

def list_templates() -> list[str]:
    return list(FILE_TEMPLATES.keys())
```

---

## References

- `code-generation-templates-skill/SKILL.md` — kod üretim şablonları
- `project-file-structure-skill/SKILL.md` — proje dosya yapısı
- `schema-first-design-skill/SKILL.md` — şema öncelikli tasarım
