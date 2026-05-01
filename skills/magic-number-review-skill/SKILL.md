---
name: magic-number-review
description: Planner AI için — kodun içindeki anlamsız sayısal ve string sabitlerini tespit etmek; bunları isimlendirilmiş sabit veya config değerine dönüştürmek.
---

## Purpose

Anlamsız literal değerleri yakalar.
`600` nedir? `3` ne anlama geliyor? İsimsiz sabit okumayı ve değiştirmeyi zorlaştırır.
Değer birden fazla yerde kullanılıyorsa tek yerden yönetilmeli.

---

## When to Apply

- Sayısal literal (`600`, `3`, `15`, `0.5`) içeren kod review edilirken
- Hardcode string (`"pending"`, `"worker_a"`) görüldüğünde
- Timeout, limit, threshold değerleri review edilirken

---

## Rules

- Business anlamı olan her sayısal değer isimlendirilmiş sabite dönüşür.
- Config'den gelmesi gereken değerler `settings.py`'e eklenir.
- Enum olması gereken string'ler enum'a dönüştürülür.
- Matematiksel sabitler (0, 1, -1) ve açık anlamlılar (`len(list)`) muaf.

---

## Guidelines

Magic number tespiti:
```python
# YANLIŞ — magic number
if state.get("review_cycles", 0) >= 3:  # 3 ne?
    return END
await asyncio.sleep(600)  # 600 saniye neden?
if attempt_count > 3:  # 3 yine?
    mark_failed()

# DOĞRU — isimlendirilmiş sabit
MAX_REVIEW_CYCLES = 3
STALL_TIMEOUT_SECONDS = 600
MAX_WORKER_RETRIES = 3

if state.get("review_cycles", 0) >= MAX_REVIEW_CYCLES:
    return END
await asyncio.sleep(STALL_TIMEOUT_SECONDS)
if attempt_count > MAX_WORKER_RETRIES:
    mark_failed()
```

Config'e taşınması gerekenler:
```python
# settings.py'e ekle
class Settings(BaseSettings):
    MAX_REVIEW_CYCLES: int = 3
    STALL_TIMEOUT_SECONDS: int = 600
    WORKER_TIMEOUT_SECONDS: int = 30
    APPROVAL_TIMEOUT_MINUTES: int = 15
    EVENT_HISTORY_SIZE: int = 500
```

Hardcode string magic values:
```python
# YANLIŞ
if status == "planned":  # string literal
    worker_id = "worker_a"  # hardcode

# DOĞRU
class FileStatus(str, Enum):
    PLANNED = "planned"
    RESERVED = "reserved"

WORKER_IDS = ["worker_a", "worker_b", "worker_c"]

if status == FileStatus.PLANNED:
    worker_id = WORKER_IDS[0]
```

---

## References

- `constant-extraction-skill/SKILL.md` — sabit çıkarma
- `pydantic-settings-definition-skill/SKILL.md` — config değerleri
- `enum-definition-skill/SKILL.md` — enum kullanımı
