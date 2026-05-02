---
name: http-client-patterns
description: Coder AI için — async HTTP istekleri yapmak; httpx.AsyncClient veya aiohttp ile doğru session yönetimi ve timeout ayarı.
---

## Purpose

Async HTTP istemcisi yanlış kullanılırsa connection leak veya deadlock olur.
Session tek seferlik oluşturulup paylaşılır — her istek için yeni session açılmaz.
Timeout ayarlanmazsa istek sonsuza kadar asılı kalabilir.

---

## When to Apply

- OpenRouter veya başka REST API'ye istek yapılırken
- Webhook endpoint'i çağrılırken
- Harici servis entegrasyonu yazılırken

---

## Rules

- `httpx.AsyncClient`: uygulama yaşam süresi boyunca tek instance.
- Timeout: bağlantı 5s, okuma 30s varsayılan.
- 4xx: retry edilmez. 5xx / timeout: retry edilir.
- Response JSON parse başarısız olursa `HTTPResponseError` fırlatılır.
- API key: header'a eklenir — URL'ye konmaz.

---

## Guidelines

```python
import httpx
from typing import Any

DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)

class HTTPClient:
    def __init__(self, base_url: str, api_key: str | None = None):
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
    
    async def post(self, path: str, json: dict) -> dict[str, Any]:
        response = await self._client.post(path, json=json)
        
        if response.status_code >= 400:
            raise HTTPResponseError(
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
        
        try:
            return response.json()
        except Exception as e:
            raise HTTPResponseError(f"JSON parse hatası: {e}") from e
    
    async def aclose(self) -> None:
        await self._client.aclose()

class HTTPResponseError(Exception):
    pass
```

Lifecycle yönetimi (lifespan):
```python
http_client: HTTPClient | None = None

async def startup():
    global http_client
    http_client = HTTPClient(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )

async def shutdown():
    if http_client:
        await http_client.aclose()
```

---

## References

- `provider-fallback-chain-skill/SKILL.md` — provider geçişi
- `retry-decorator-implementation-skill/SKILL.md` — retry
- `async-context-manager-skill/SKILL.md` — kaynak yönetimi
