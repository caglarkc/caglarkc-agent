---
name: code-mode
description: AI Development Team Orchestrator projesinde Codex'in kod yazma kuralları. Claude'dan gelen görev prompt'larını alır, analiz eder, projenin mimarisine uygun kod yazar ve standart formatta teslim eder. Her kodlama görevinde bu skill kullanılır.
---

## Purpose

Codex'i bu projede **uygulayıcı senior developer** gibi çalıştırmak için kullanılır.

Ana hedef:
- Claude'dan gelen görev prompt'unu eksiksiz uygulamak
- Proje mimarisine uymak
- Standart çıktı formatında teslim etmek
- Açık hataları ve eksikleri not düşmek

---

## Görev Alım Süreci

Her görev başlamadan önce şu 4 başlık kısa verilir:

```
NE İSTENDİ: <tek cümle>
HANGİ DOSYALAR ETKİLENECEK: <path listesi>
RİSKLER: <varsa>
YAPILACAKLAR: <adım listesi>
```

---

## Rules

- **Analiz önce zorunlu**: Kod yazmadan önce 4 başlık verilir.
- **Mimari uyum zorunlu**: `project-architecture` kuralları bozulmaz.
- **Async zorunlu**: Tüm I/O işlemleri async/await ile yazılır. Blocking call yasak.
- **Type hint zorunlu**: Tüm fonksiyon parametreleri ve dönüş tipleri yazılır.
- **Hata handling zorunlu**: Her dış bağlantı (API, dosya, DB) try/except ile sarılır.
- **Bağımlılık kuralı**: Sadece `pyproject.toml`'da tanımlı paketler kullanılır. Yeni paket gerekiyorsa not düşülür, kurulmaz.
- **Dosya sınırı**: Her worker kendi alanı dışına yazmaz. (`project-architecture` referans)
- **Yorum dili**: Kod içi yorumlar Türkçe yazılır.
- **Test yazma**: Claude açıkça istemedikçe test dosyası oluşturulmaz. Manuel kontrol notu bırakılır.
- **Commit yasağı**: Codex commit atmaz. Sadece dosya teslim eder.

---

## Katman Kuralları

### LangGraph Katmanı (`src/graph/`)
- `planner → dispatcher → workers → validator → reviewer` akışı korunur
- Her node async fonksiyon — state alır, dict döner (sadece değiştirilen alanlar)
- Worker node'lar `file_registry`'de rezerve edilmiş dosyaya yazar, başkasına dokunamaz
- Koşullu edge fonksiyonları `edges.py`'de tanımlanır, node içine yazılmaz
- Referans: `langgraph-patterns/SKILL.md`

### Interface Katmanı (`src/interfaces/`)
- Telegram ve CLI aynı `EventBus`'a bağlanır
- Her interface kendi modülünde izole çalışır
- Interface'ler direkt LangGraph'a erişmez, EventBus üzerinden iletişim kurar
- Referans: `telegram-bot-patterns/SKILL.md`

### Core Katmanı (`src/core/`)
- `EventBus`, `StateManager`, `ProjectManager` burada yaşar
- Singleton pattern kullanılır
- Tüm state değişiklikleri `StateManager` üzerinden yapılır

### Config Katmanı (`src/config/`)
- API key'ler ve ayarlar `.env` üzerinden okunur
- Hardcode değer yasak
- `pydantic-settings` ile config doğrulanır

---

## Async Kuralları

```python
# DOĞRU
async def call_api(self) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response.json()

# YANLIŞ - blocking call
def call_api(self) -> dict:
    response = requests.get(url)  # yasak
    return response.json()
```

- `asyncio.run()` sadece `main.py` entry point'te kullanılır
- `await` olmayan async fonksiyon yazılmaz
- Paralel işlemler `asyncio.gather()` ile yapılır
- Referans: `python-async-patterns/SKILL.md`

---

## Teslim Formatı

Görev bittikten sonra şu formatta teslim edilir:

```
YAPILAN İŞ:
- <kısa özet>

DEĞİŞEN DOSYALAR:
- <path> — <ne değişti>
- <path> — <yeni dosya>

AKTİF DAVRANIŞLAR:
- <kullanıcı açısından ne çalışıyor>

BEKLENEN EKLEMELER:
- <env key, config, asset — yoksa YOK>

MANUEL KONTROL:
- <nasıl test edilir>
- <dikkat edilecek edge case>

NOTLAR:
- <mimari sapma varsa>
- <eksik bırakılan şey varsa>
- <yeni paket gerekiyorsa>
```

---

## References

- `project-architecture/SKILL.md` — zorunlu, her görevde referans alınır
- `langgraph-patterns/SKILL.md` — LangGraph kodu yazarken
- `python-async-patterns/SKILL.md` — async kod yazarken
- `telegram-bot-patterns/SKILL.md` — Telegram/CLI kodu yazarken