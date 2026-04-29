# Phase 1 Acceptance Notes

This repository's Phase 1 smoke validation is centered on `scripts/check_connections.py`.

What the script verifies:
- Gemini connectivity through the LangChain `ChatGoogleGenerativeAI` adapter
- Ollama connectivity through the LangChain `ChatOllama` adapter
- OpenRouter primary and secondary key connectivity through the LangChain `ChatOpenAI` adapter
- LangGraph `AsyncSqliteSaver` checkpoint persistence
- Minimal `planner -> worker -> reviewer` graph completion

Acceptance output contract:
- Each check prints `PASS` or `FAIL`
- Missing credentials stay as controlled `FAIL` messages
- The script ends with a fixed acceptance summary block
- `PHASE_1_STATUS` is `READY` only when all checks pass
