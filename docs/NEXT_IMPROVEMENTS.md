# Sonraki Geliştirmeler

## 1. Worker'a Tool Calling (Bilgisayar Erişimi)

**Neden:** Worker şu an kör kod üretiyor — yazdığı kodun çalışıp çalışmadığını bilmiyor.

**Ne yapılacak:**
- `src/core/llm_providers.py` içine `execute_bash`, `read_file`, `write_file` tool'ları eklenecek
- Worker LLM'i bu tool'larla bağlanacak: `ChatOllama(...).bind_tools([execute_bash, ...])`
- Qwen2.5-coder Ollama 0.3+ ile tool calling destekliyor

**Dosyalar:** `src/core/llm_providers.py`, `src/graph/nodes/worker.py`

---

## 2. LangGraph'a Executor Node

**Neden:** Şu an Validator sadece syntax kontrolü yapıyor, kodu gerçekten çalıştırmıyor.

**Ne yapılacak:**
- Graph akışına yeni bir `executor` node eklenecek
- Akış: `Worker → Executor → Validator → Reviewer`
- Executor kodu terminal'de çalıştırır, çıktıyı/hatayı state'e yazar
- Hata varsa Worker'a geri döner (otomatik düzeltme döngüsü)

**Dosyalar:** `src/graph/nodes/executor.py` (yeni), `src/graph/graph.py`, `src/graph/edges.py`, `src/graph/state.py`

---

## Not: Gemini Lokal Taşıma (Şimdilik Beklemede)

Planner ve Reviewer rolü şimdilik Gemini'de kalıyor. İleride lokal Qwen3.5:9b veya daha büyük bir model (14b+) yeterince iyi olursa devralabilir. Şu an tradeoff yok sayılmayacak kadar büyük.
