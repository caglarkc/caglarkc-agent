---
name: docstring-generation
description: Coder AI için — fonksiyon ve sınıflara kısa, bilgilendirici docstring eklemek; parametre ve dönüş tiplerini açıklamak.
---

## Purpose

Docstring olmayan kod bakımı zorlaştırır.
İyi docstring, fonksiyonun ne yaptığını ve parametrelerini açıklar.
Bu projede Türkçe yorum, İngilizce docstring karışımı tercih edilir.

---

## When to Apply

- Public fonksiyon veya sınıf yazılırken
- Karmaşık mantık içeren node veya helper yazılırken
- Repository metodu oluşturulurken

---

## Rules

- Tek satır docstring: basit fonksiyonlar için yeterli.
- Multi-line: parametreler ve dönüş değeri önemliyse.
- `Args` ve `Returns` sadece non-obvious durumlarda.
- Örnek kod docstring'e eklenmez — uzatır.
- `Raises` bölümü: sadece kasıtlı fırlatılan exception'lar için.

---

## Guidelines

```python
# Basit fonksiyon — tek satır yeterli
async def get_sprint(self, sprint_id: str) -> Sprint | None:
    """sprint_id'ye göre sprint döndürür, bulunamazsa None."""
    ...

# Karmaşık fonksiyon — multi-line
async def dispatch_files(
    state: OrchestratorState,
    max_concurrent: int = 3
) -> list[str]:
    """
    Planned dosyaları worker kuyruğuna atar.

    Args:
        state: Mevcut orchestrator durumu.
        max_concurrent: Paralel işlenecek maksimum dosya sayısı.

    Returns:
        Kuyruğa eklenen dosya yollarının listesi.

    Raises:
        InvalidStateTransition: Dosya reserved yapılamazsa.
    """
    ...

# Sınıf docstring
class ProjectRepository:
    """aiosqlite tabanlı proje CRUD operasyonları."""
    ...
```

Node docstring formatı:
```python
async def planner_node(state: OrchestratorState) -> OrchestratorState:
    """
    Kullanıcı isteğini sprint planına dönüştürür.

    LLM'e mevcut state ve geçmiş kararları göndererek
    görev listesi ve dosya listesi üretir.
    """
    ...
```

---

## References

- `code-mode-skill/SKILL.md` — genel kod kuralları
- `node-function-signature-skill/SKILL.md` — node imzası
- `type-annotation-patterns-skill/SKILL.md` — tip ipuçları
