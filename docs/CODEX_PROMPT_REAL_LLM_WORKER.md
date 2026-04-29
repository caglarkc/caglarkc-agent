# Codex için: Gerçek LLM ile worker entegrasyonu

Bu dosyayı yeni bir sohbette aşağıdaki blok olarak yapıştırabilirsin. Repo kökü: **`caglarkc-agent`** (path’i kendi makinede güncelle).

---

## Görev

Bu repoda **`src/graph/nodes/worker.py`** içinde `_render_file_content()` ile sabit şablon basılıyor. **Gerçek üretim**: `.env` içindeki API anahtarları kullanılarak LangChain adapter’ları üzerinden kod/dosya içeriği üretilecek.

**Hedef:**

1. `worker_a` → **Ollama** (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`)
2. `worker_b` → **OpenRouter Primary** (`OPENROUTER_API_KEY_PRIMARY`, `OPENROUTER_MODEL`; mevcut ayar alanları)
3. `worker_c` → **OpenRouter Secondary** (`OPENROUTER_API_KEY_SECONDARY` + **ayrı model alanı** — şu an `.env`’de `OPENROUTER_MODEL_SECONDARY` var ama **Settings’te yok**; ekle: `openrouter_model_secondary: str` + `.env.example`)

Opsiyonel / genişletme: İlk sprint “contract” dosyalarında kalite için **Gemini** kullanımı (`GEMINI_API_KEY`, `GEMINI_MODEL`) — bunu `assignment.metadata` veya `worker_id` ile politika olarak netleştir veya sadece feature sprint’te LLM aç (minimum scope: sadece worker_* LLM, stub fallback **yalnızca anahtar yoksa**).

2. **Prompt içeriği mutlaka kullanıcı niyetini içersin:** `state["task_description"]`, `assignment.description`, `state.get("context_summary")` (kısaltılmış), dosya yolu, sprint tipi (`state.get("sprint_type")`). Çıktı tek dosya gövdesi olmalı; Markdown fence veya açıklama metni ekleme — validator path/syntax bozulmasın.

3. **LangChain:** Mevcut stack: `langchain-google-genai`, `langchain-community`, `langchain-openai`. Referans: `scripts/check_connections.py` (ChatGoogleGenerativeAI, ChatOllama, ChatOpenAI + OpenRouter base URL).

4. **Async:** Worker node async; `await model.ainvoke(...)` veya Runnable kullan.

5. **Hata işleme:** Mevcut `RetryPolicy`, `classify_error`, reservation ve file_registry akışına dokunma; LLM çağrısı başarısız olursa mevcut exception yoluyla retry/failure log’a düşsün.

6. **Güvenlik:** Prompt ve log’da API key sızdırma; üretilen içerikte path traversal / `..` politikalarına validator uyumlu kal.

7. **Yeni modül:** `src/graph/llm_worker.py` veya `src/core/llm_providers.py` gibi tek yerde model fabrikası (worker_id → chat model instance + system prompt şablonu). `worker.py` sadece orchestration + `write_project_file` kalsın.

8. **Test:** `scripts/check_connections.py` zaten gerçek API’leri ping’liyor; mümkünse `check_phase4`/`check_phase3` regresyonu bozma. Gerekirse `WORKER_USE_STUB=1` env ile eski davranışı testlerde aç/kapa (isteğe bağlı).

9. **Dokümantasyon:** `docs/PHASE_ACCEPTANCE.md` veya kısa `docs/REAL_WORKER.md` içinde: hangi worker hangi provider, `.env` değişkenleri, `.env.example` güncelle.

**Kabul kriterleri:**

- `task_description` ile verilen görev, üretilen dosya içeriğinde anlamlı şekilde yansır (smoke’ta sabit şablon yerine LLM çıktısı).
- Üç worker farklı slot’larda farklı provider kullanır (dispatcher `worker_a/b/c` döngüsü ile).
- Anahtar eksik provider düzgün FAIL / fallback mesajı (mevcut Retry semantiğiyle uyumlu).

**Değişecek / eklenecek dosyalar (öneri):**

- `src/graph/nodes/worker.py` — `_render_file_content` → `await generate_file_content(...)`
- `src/config/settings.py` — `OPENROUTER_MODEL_SECONDARY`
- `.env.example` — aynı
- `src/core/llm_providers.py` (yeni) veya benzeri
- İsteğe bağlı küçük unit: `tests/test_llm_prompt_build.py`

**Yapmayacakların:**

- Planner/reviewer/graph edge sözleşmesini geniş çaplı refactor etme.
- API key’leri repoya commit etme.

---

Bittiğinde komutlar: `PYTHONPATH=. .venv/bin/python scripts/check_phase3.py` ve manuel `python main.py --cli` ile bir `/task` akışı.
