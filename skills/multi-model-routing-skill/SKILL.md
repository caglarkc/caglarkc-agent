---
name: multi-model-routing
description: Coder AI için — görev tipine ve karmaşıklığa göre farklı LLM modellerine otomatik yönlendirme yapmak; maliyet-kalite dengesini optimize etmek.
---

## Purpose

Her görev için en pahalı modeli kullanmak israf.
Basit görevler: küçük/hızlı model. Karmaşık görevler: güçlü model.
Routing mantığı: görev tipi → model seçimi → çağrı.

---

## When to Apply

- Farklı karmaşıklıkta görevler için farklı model kullanmak istendiğinde
- Maliyet optimizasyonu yapılırken
- Model portfolio genişletildiğinde

---

## Rules

- Basit (S): Gemini Flash veya Ollama küçük model.
- Orta (M): Gemini Flash veya Ollama büyük model.
- Karmaşık (L): Gemini Pro veya OpenRouter güçlü model.
- Review: her zaman güçlü model (kalite kritik).
- Fallback: tercih edilen model yoksa bir üst sınıfa geç.

---

## Guidelines

```python
from enum import Enum

class ModelTier(str, Enum):
    FAST     = "fast"      # Hızlı, ucuz
    BALANCED = "balanced"  # Dengeli
    POWERFUL = "powerful"  # Güçlü, pahalı

TASK_TO_TIER = {
    "simple_code":   ModelTier.FAST,
    "complex_code":  ModelTier.BALANCED,
    "architecture":  ModelTier.POWERFUL,
    "review":        ModelTier.POWERFUL,
    "planning":      ModelTier.BALANCED,
    "conversation":  ModelTier.FAST,
}

TIER_TO_MODEL = {
    ModelTier.FAST: {
        "gemini": "gemini-2.0-flash",
        "ollama": "codellama:7b",
        "openrouter": "meta-llama/llama-3.1-8b-instruct",
    },
    ModelTier.BALANCED: {
        "gemini": "gemini-2.5-flash",
        "ollama": "codellama:13b",
        "openrouter": "deepseek/deepseek-coder",
    },
    ModelTier.POWERFUL: {
        "gemini": "gemini-2.5-pro",
        "ollama": "codellama:34b",
        "openrouter": "anthropic/claude-sonnet-4-5",
    },
}

def route_model(
    task_type: str,
    provider: str,
) -> str:
    tier = TASK_TO_TIER.get(task_type, ModelTier.BALANCED)
    models = TIER_TO_MODEL[tier]
    return models.get(provider, models["openrouter"])

def create_routed_llm(
    task_type: str,
    settings: Settings,
) -> BaseChatModel:
    tier = TASK_TO_TIER.get(task_type, ModelTier.BALANCED)
    
    if settings.ollama_base_url:
        model_name = TIER_TO_MODEL[tier]["ollama"]
        return ChatOllama(base_url=settings.ollama_base_url, model=model_name)
    
    model_name = TIER_TO_MODEL[tier]["gemini"]
    return ChatGoogleGenerativeAI(model=model_name, google_api_key=settings.gemini_api_key)
```

---

## References

- `llm-provider-selection-skill/SKILL.md` — provider seçimi
- `llm-temperature-tuning-skill/SKILL.md` — temperature
- `task-estimation-calibration-skill/SKILL.md` — karmaşıklık
