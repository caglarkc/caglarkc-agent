---
name: telemetry-logging
description: Coder AI için — LLM çağrılarının süresini, token kullanımını ve sonucunu loglayarak maliyet ve performans takibi yapmak.
---

## Purpose

Hangi LLM çağrısı ne kadar sürdü ve kaç token harcadı bilinmezse optimizasyon yapılamaz.
Telemetri logu maliyet tahminini ve darboğaz tespitini sağlar.
Production'da LangSmith veya basit log dosyasına yazılır.

---

## When to Apply

- LLM çağrısı yapıldığında wrapper ile zamanlama ve token ölçümü yapılırken
- Maliyet raporlama özelliği eklenirken
- Yavaş LLM çağrısı tespit edilirken

---

## Rules

- Her LLM çağrısı: başlangıç/bitiş zamanı, token sayısı, sonuç.
- Başarısız çağrılar: hata türü ile loglanır.
- Telemetri log'u: ayrı dosyaya yazılabilir (performance.log).
- Token sayısı: response metadata'dan okunur.

---

## Guidelines

```python
import time
from dataclasses import dataclass

@dataclass
class LLMCallTelemetry:
    node_name: str
    model: str
    duration_ms: float
    input_tokens: int
    output_tokens: int
    success: bool
    error: str | None = None

async def timed_llm_invoke(
    llm: BaseChatModel,
    messages: list,
    node_name: str = "unknown",
) -> BaseMessage:
    start = time.perf_counter()
    
    try:
        response = await llm.ainvoke(messages)
        duration_ms = (time.perf_counter() - start) * 1000
        
        # Token bilgisi (model destekliyorsa)
        usage = getattr(response, "usage_metadata", {}) or {}
        
        telemetry = LLMCallTelemetry(
            node_name=node_name,
            model=getattr(llm, "model", "unknown"),
            duration_ms=duration_ms,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            success=True,
        )
        log_telemetry(telemetry)
        return response
    
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        telemetry = LLMCallTelemetry(
            node_name=node_name,
            model=getattr(llm, "model", "unknown"),
            duration_ms=duration_ms,
            input_tokens=0,
            output_tokens=0,
            success=False,
            error=type(e).__name__,
        )
        log_telemetry(telemetry)
        raise

def log_telemetry(t: LLMCallTelemetry) -> None:
    logger.info(
        f"LLM | {t.node_name} | {t.model} | "
        f"{t.duration_ms:.0f}ms | "
        f"in:{t.input_tokens} out:{t.output_tokens} | "
        f"{'OK' if t.success else 'ERR:' + str(t.error)}"
    )
```

---

## References

- `logging-patterns-skill/SKILL.md` — genel loglama
- `sprint-metrics-collection-skill/SKILL.md` — sprint metrikleri
- `llm-provider-selection-skill/SKILL.md` — provider seçimi
