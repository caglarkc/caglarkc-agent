---
name: provider-fallback-chain
description: Coder AI için — LLM provider fallback zincirini (Ollama → OpenRouter Primary → Secondary → Stub) doğru implemente etmek; her provider'ın bağımsız denemesi ve hata yönetimi.
---

## Purpose

`src/core/llm_providers.py`'deki provider fallback mantığını standartlaştırır.
Primary provider başarısız olursa otomatik secondary'ye geçer.
Stub fallback her zaman çalışır — sistem hiç yanıt vermemekten iyidir.

---

## When to Apply

- `generate_file_content()` veya LLM çağrısı yapan fonksiyon yazılırken
- Yeni LLM provider eklenirken
- Fallback zinciri değiştirilirken

---

## Rules

- Zincir sırası: Ollama → OpenRouter Primary → OpenRouter Secondary → Stub.
- Her provider ayrı try/except bloğu.
- Provider başarısız olduğunda sadece `warning` log — exception fırlatılmaz.
- Son fallback (stub): her zaman başarılı olur, `used_stub=True` flag set edilir.
- Provider seçimi `worker_id`'ye göre yapılabilir (worker_a → Ollama öncelikli).
- API key yoksa o provider atlanır.

---

## Guidelines

Fallback zinciri implementasyonu:
```python
async def generate_file_content(
    worker_id: str,
    task: dict,
    context: str
) -> GeneratedFileContent:
    providers = _get_provider_chain(worker_id)
    
    for provider_name, provider_func in providers:
        try:
            content = await provider_func(task, context)
            logger.info(f"Provider kullanıldı: {provider_name}", extra={"worker_id": worker_id})
            return GeneratedFileContent(
                content=content,
                provider=provider_name,
                model=_get_model(provider_name),
                used_stub=False
            )
        except RetryableError as e:
            logger.warning(f"{provider_name} geçici hata: {e}, sonraki provider deneniyor")
            continue
        except PermanentError as e:
            logger.error(f"{provider_name} kalıcı hata: {e}, sonraki provider deneniyor")
            continue
    
    # Tüm provider'lar başarısız → stub fallback
    logger.warning("Tüm provider'lar başarısız, stub kullanılıyor", extra={"worker_id": worker_id})
    return GeneratedFileContent(
        content=_render_stub_content(task),
        provider="stub",
        model="template",
        used_stub=True
    )


def _get_provider_chain(worker_id: str) -> list[tuple[str, Callable]]:
    chain = []
    settings = get_settings()
    
    if settings.ollama_base_url:
        chain.append(("ollama", _call_ollama))
    if settings.openrouter_api_key_primary:
        chain.append(("openrouter_primary", _call_openrouter_primary))
    if settings.openrouter_api_key_secondary:
        chain.append(("openrouter_secondary", _call_openrouter_secondary))
    
    return chain
```

---

## References

- `rate-limit-handling-skill/SKILL.md` — rate limit
- `custom-exception-hierarchy-skill/SKILL.md` — exception tipleri
- `prompt-construction-pattern-skill/SKILL.md` — prompt yapısı
