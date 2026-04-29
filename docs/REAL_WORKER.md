# Real Worker LLM Integration

Workers now generate file bodies through LangChain chat adapters instead of a fixed template.

## Provider Mapping

- `worker_a`: Ollama via `OLLAMA_BASE_URL` and `OLLAMA_MODEL`.
- `worker_b`: OpenRouter primary via `OPENROUTER_API_KEY_PRIMARY`, `OPENROUTER_BASE_URL`, and `OPENROUTER_MODEL`.
- `worker_c`: OpenRouter secondary via `OPENROUTER_API_KEY_SECONDARY`, `OPENROUTER_BASE_URL`, and `OPENROUTER_MODEL_SECONDARY`.

## Prompt Contract

The worker prompt includes the original `task_description`, the assignment description, the compacted `context_summary`, the target file path, and the sprint type. Models are instructed to return only the raw file body with no Markdown fences or explanation text so validator syntax and path policy checks remain deterministic.

## Fallbacks

Set `WORKER_USE_STUB=1` for deterministic local smoke tests. If an OpenRouter worker is selected without its API key, the worker writes the deterministic fallback content and records the fallback reason in state messages. Provider invocation errors are not swallowed; they continue through the existing retry and failure logging path.
