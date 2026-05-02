---
name: lazy-loading
description: Coder AI için — ağır bağımlılıkları (LLM client, DB bağlantısı) sadece ilk kullanıldığında yüklemek; startup süresini kısaltmak.
---

## Purpose

Tüm bağımlılıklar startup'ta yüklenirse başlangıç yavaşlar.
Lazy loading, LLM client'ı ilk gerçek çağrıda oluşturur.
Test ortamında gereksiz bağlantı kurulmaz.

---

## When to Apply

- LLM client, DB bağlantısı veya ağır modül startup'ta yüklenirken
- Test ortamında gerçek bağlantıların engellenmesi gerektiğinde
- Startup süresi optimize edilirken

---

## Rules

- Lazy singleton: ilk çağrıda oluştur, sonrakilerde cachelden ver.
- Thread-safe değil (asyncio single-thread — sorun değil).
- None check ile initialized olup olmadığı kontrol edilir.
- Teardown: shutdown sırasında kaynaklar temizlenir.

---

## Guidelines

```python
class LLMFactory:
    _planner_llm: BaseChatModel | None = None
    _coder_llm: BaseChatModel | None = None
    
    @classmethod
    def get_planner_llm(cls, settings: Settings) -> BaseChatModel:
        if cls._planner_llm is None:
            logger.info("Planner LLM başlatılıyor...")
            cls._planner_llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.gemini_api_key,
                temperature=0.2,
            )
        return cls._planner_llm
    
    @classmethod
    def get_coder_llm(cls, settings: Settings) -> BaseChatModel:
        if cls._coder_llm is None:
            logger.info("Coder LLM başlatılıyor...")
            cls._coder_llm = ChatOllama(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )
        return cls._coder_llm
    
    @classmethod
    def reset(cls) -> None:
        """Test için sıfırla."""
        cls._planner_llm = None
        cls._coder_llm = None

# Lazy DB repository
_repo: ProjectRepository | None = None

def get_repository(settings: Settings) -> ProjectRepository:
    global _repo
    if _repo is None:
        _repo = ProjectRepository(settings.db_path)
    return _repo
```

---

## References

- `dependency-injection-patterns-skill/SKILL.md` — DI
- `settings-validation-skill/SKILL.md` — settings
- `healthcheck-endpoint-skill/SKILL.md` — bileşen durumu
