# ARCHON

> **Autonomous Multi-Agent Software Development Orchestrator**

ARCHON is a production-grade, LangGraph-powered orchestration system that coordinates multiple AI models to autonomously plan, generate, validate, and review software projects — with human approval gates at every critical decision point.

You act as **Tech Lead**. ARCHON handles the rest: a Gemini-powered **Planner** breaks down your request, **Workers** (Ollama / OpenRouter / Gemini) generate the code, and an automated **Validator → Reviewer** loop ensures quality before anything ships.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Agent Pipeline](#agent-pipeline)
- [LLM Providers](#llm-providers)
- [Interfaces](#interfaces)
- [Skills Library](#skills-library)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [CLI Command Reference](#cli-command-reference)
- [Project Structure](#project-structure)
- [Key Design Principles](#key-design-principles)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          ARCHON DAEMON                          │
│                                                                 │
│   ┌──────────┐     ┌────────────────────────────────────────┐  │
│   │ Telegram │     │         LangGraph State Machine        │  │
│   │   Bot    │     │                                        │  │
│   └────┬─────┘     │  planner → dispatcher → worker ──┐    │  │
│        │           │                                   ↓    │  │
│   ┌────┴─────┐     │                              executor  │  │
│   │ Textual  │     │                                   ↓    │  │
│   │  TUI CLI │     │                             validator  │  │
│   └────┬─────┘     │                                   ↓    │  │
│        │           │                              reviewer  │  │
│        │           │                                   ↓    │  │
│   ┌────┴─────┐     │                          [done/retry]  │  │
│   │ EventBus │◄────┤                                        │  │
│   └──────────┘     └────────────────────────────────────────┘  │
│                                                                 │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│   │  Gemini  │  │  Ollama  │  │OpenRouter│  │   SQLite    │  │
│   │ (Planner)│  │ (Worker) │  │ (Worker) │  │ Checkpoint  │  │
│   └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

ARCHON is built on three layers:

| Layer | Components |
|---|---|
| **Orchestration** | LangGraph state machine, GraphManager, StateManager, EventBus |
| **Intelligence** | ManagerPlanningService (Gemini), LLM worker chain, FinalReview auditor |
| **Infrastructure** | SQLite persistence, RetryPolicy, ApprovalGuard, AIScanner health checks |

---

## Agent Pipeline

Each task flows through a deterministic six-node pipeline. The graph is stateful: every transition is persisted to SQLite and can be resumed after a crash.

### 1. Planner
Receives your message and conversation history. Calls **Gemini** to produce a `PlanDraft` — a structured list of files, types, and dependencies — and determines whether to discuss further or proceed to execution. Routes to the **Approval Gate** when execution intent is detected.

```
Input : task_description, conversation_history
Output: draft_plan (files + dependencies), manager_reply, awaiting_approval
```

### 2. Dispatcher
Inspects the worker queue, detects dependency cycles, selects the idle worker with the lowest failure count, and atomically reserves a file for generation. Prevents concurrent writes via a file reservation system.

```
Input : worker_queue, dependency graph, file_registry
Output: active_assignment, updated worker_status
```

### 3. Worker
Calls the configured LLM chain (Ollama → OpenRouter → Gemini fallback) with a context-rich prompt that includes task description, related file snapshots, previous validation errors, and output safety rules. Saves the generated file to the project filesystem.

```
Input : active_assignment, validation_issues (from prior cycles)
Output: worker_outputs, file_registry update (in_progress → done/failed)
```

### 4. Executor
Runs the project's build/test command (Python `pytest`, Node `npm test`, etc.) inside a 20-second timeout sandbox. Captures stdout/stderr for the Reviewer.

```
Input : file_registry (done files), project root
Output: execution_results, runtime_errors
```

### 5. Validator
Performs static analysis on all generated files: AST syntax checks, import resolution, and policy rules (path traversal detection, prompt injection patterns). Writes `validation_issues` back to state.

```
Input : project files, worker_queue
Output: validation_issues, revision_tasks
```

### 6. Reviewer
Calls the **Gemini auditor** (`FinalReview`) to inspect generated files holistically. Decides one of:
- **active** → sprint complete, close successfully
- **revision** → re-queue failed files, loop back to Dispatcher (max 6 cycles)
- **fail** → terminal failure after exhausting retries

```
Input : validation_issues, execution_results, review_cycles
Output: sprint_status ∈ {active, revision, fail, closed, rejected}
```

### Post-sprint Memory / Dreaming (Background)

After the **Reviewer** reaches a terminal sprint decision (`approved` / `fail`), ARCHON schedules a **non-blocking** background memory pipeline:

- **Extract**: writes a durable sprint summary Markdown into `projects/<name>/.meta/memory/extracts/`
- **Consolidate** (gated + locked): merges recent extracts into a planner-facing memory file (default: `planner_memory.md`)
- **Inject**: `ContextBuilder` includes a short slice as `[Tier0] Planner Memory: ...` in future Planner prompts

The consolidation step is protected by:
- **time gate** (`MEMORY_MIN_HOURS_BETWEEN_RUNS`)
- **activity gate** (`MEMORY_MIN_SESSIONS`, based on sprint snapshot mtimes under `.meta/sprints/`)
- **lock file** (`.consolidate-lock`, mtime = last successful consolidation)

### Approval Gate

Before any Worker phase starts, ARCHON waits for human approval. The gate is **idempotent** — duplicate approvals are rejected via `idempotency_key`. Approvals expire after 15 minutes.

```
/approve [approval_id]   → resumes graph at Dispatcher
/reject  [approval_id]   → terminal state: planning_status = rejected
/cancel  [approval_id]   → terminal state: planning_status = cancelled
```

---

## LLM Providers

ARCHON supports a **fallback chain** across three provider types. If a provider fails or is unavailable, the next one in the chain is tried automatically.

| Provider | Role | Notes |
|---|---|---|
| **Gemini** (Google) | Planner, Auditor, Worker fallback | Primary intelligence layer |
| **Ollama** (local) | Worker (primary) | Zero-cost local inference; auto-detected at startup |
| **OpenRouter** (Primary) | Worker | Free/paid model via OpenRouter API |
| **OpenRouter** (Secondary) | Worker fallback | Secondary key + model for redundancy |

**Fallback order for Workers**: Ollama → OpenRouter Primary → OpenRouter Secondary → Gemini stub

The `AIScanner` (`/scan` command) probes all providers simultaneously and reports latency + token metrics before you start a sprint.

---

## Interfaces

### Textual TUI (CLI)

A full-featured terminal UI powered by [Textual](https://textual.textualize.io/). Real-time event updates via EventBus. Supports all commands below.

```bash
python main.py --cli --no-telegram
```

### Telegram Bot

Full workflow mirroring the CLI, accessible from any device. Requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

```bash
python main.py  # daemon mode, Telegram active if token is set
```

### Daemon Mode

Runs as a background service with signal handlers (SIGINT/SIGTERM), heartbeat writes, PID file management, and automatic thread recovery on startup.

```bash
python main.py --cli          # TUI + Telegram + daemon
python main.py --no-telegram  # TUI only
python main.py                # Headless daemon (Telegram only)
```

---

## Skills Library

ARCHON ships with **360 skill files** in `skills/` — structured knowledge documents for Planner AI and Coder AI covering every pattern used in the system.

| Category | Examples |
|---|---|
| Sprint Lifecycle | planning, approval-gate, capacity-planning, risk-register, retrospective |
| LangGraph Patterns | subgraph, node-error-boundary, hot-reload, state-persistence-recovery |
| Async Python | asyncio-gather, async-context-manager, async-semaphore-throttling |
| Code Quality | ast-manipulation, dead-code-detection, naming-convention, complexity-metric |
| LLM Integration | prompt-chaining, few-shot-examples, response-streaming, tool-use-pattern |
| Testing | test-data-builder, test-fixture-cleanup, coverage-check |
| Security | api-key-masking, code-security-scan, environment-guard |

See [`SKILLS_INDEX.md`](SKILLS_INDEX.md) for the full annotated list.

---

## Installation

### Prerequisites

- Python ≥ 3.11
- (Optional) [Ollama](https://ollama.ai) for local inference
- Gemini API key (free tier works)
- (Optional) OpenRouter API key(s)
- (Optional) Telegram Bot token

### Setup

```bash
# 1. Clone
git clone https://github.com/caglarkc/caglarkc-agent.git archon
cd archon

# 2. Create virtualenv
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install
pip install -e ".[dev]"

# 4. Configure
cp .env.example .env
# Edit .env — at minimum set GEMINI_API_KEY

# 5. Run preflight checks
python scripts/preflight.py

# 6. Launch
python main.py --cli --no-telegram
```

---

## Configuration

All configuration is via environment variables (`.env` file). Below are the most important settings:

```env
# ── Application ──────────────────────────────────────────────────
APP_NAME=archon
APP_ENV=development
LOG_LEVEL=INFO

# ── Storage ──────────────────────────────────────────────────────
DATA_DIR=data
PROJECTS_ROOT=projects
SQLITE_DB_PATH=data/orchestrator.db
GRAPH_CHECKPOINT_PATH=data/langgraph_checkpoints.sqlite

# ── Gemini (Planner + Auditor + Fallback Worker) ─────────────────
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-lite-latest
MANAGER_USE_GEMINI=1
MANAGER_MODEL=gemini-flash-lite-latest
MANAGER_MAX_HISTORY_TURNS=12

# ── Ollama (Local Worker) ─────────────────────────────────────────
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2                   # any model you have pulled

# ── OpenRouter (Remote Worker) ────────────────────────────────────
OPENROUTER_API_KEY_PRIMARY=your_primary_key
OPENROUTER_API_KEY_SECONDARY=your_secondary_key
OPENROUTER_MODEL=minimax/minimax-m2.5:free
OPENROUTER_MODEL_SECONDARY=tencent/hy3-preview:free

# ── Worker Behaviour ─────────────────────────────────────────────
WORKER_USE_STUB=0               # 1 = dry run (no real LLM calls)
FINAL_REVIEW_ENABLED=1
FINAL_REVIEW_TIMEOUT_SECONDS=45.0
HTTP_TIMEOUT_SECONDS=20.0

# ── Memory / Dreaming (post-sprint background pipeline) ───────────
# Writes under: projects/<project-name>/.meta/memory/
MEMORY_AUTO_ENABLED=1
MEMORY_CONSOLIDATION_ENABLED=1
MEMORY_RELATIVE_DIR=.meta/memory
MEMORY_PLANNER_SUMMARY_FILE=planner_memory.md

# Gates (cheapest → most expensive): min hours → min sessions → lock
MEMORY_MIN_HOURS_BETWEEN_RUNS=24
MEMORY_MIN_SESSIONS=5
MEMORY_SESSION_SCAN_INTERVAL_SECONDS=600
MEMORY_LOCK_HOLDER_STALE_SECONDS=3600

# Optional: use Gemini to consolidate extracts into planner memory
MEMORY_CONSOLIDATION_USE_LLM=0
MEMORY_CONSOLIDATION_MAX_INPUT_CHARS=12000

# ── Telegram ─────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

## Quick Start

```bash
# Start ARCHON
python main.py --cli --no-telegram

# Inside the TUI:

# 1. Create a new project
/new my-rest-api

# 2. Describe what you want (Turkish or English)
/r Build a FastAPI REST API with CRUD endpoints for a user table.
   Include pytest tests and a Dockerfile.

# 3. Review the generated plan
/plan

# 4. Approve and start execution
/approve

# 5. Monitor progress
/status

# 6. Browse generated files
ls projects/my-rest-api/
```

---

## CLI Command Reference

| Command | Description |
|---|---|
| `/new <name>` | Create a new project and start a conversation |
| `/r <message>` | Send a message to the Planner |
| `/plan [id]` | Request the Planner to produce / show the current draft plan |
| `/changePlan <text>` | Refine the current draft plan before approving |
| `/apply [note]` | Approve and immediately execute the current plan |
| `/approve [id]` | Approve a pending plan (resumes Dispatcher) |
| `/reject [id] [reason]` | Reject a pending plan (terminal) |
| `/cancel [id] [reason]` | Cancel a pending plan (terminal) |
| `/start [id]` | Start execution of an already-approved plan |
| `/status` | Show live state, worker assignments, and metrics |
| `/projects` | List all projects |
| `/resume [id]` | Resume an existing project thread |
| `/project use <id>` | Switch active project |
| `/history <name>` | Show conversation and sprint history |
| `/recover [id]` | Recover an interrupted execution from checkpoint |
| `/close [reason]` | Terminate the active sprint |
| `/scan` | Health-check all LLM providers (latency + tokens) |
| `/help` | Show the full command reference |

---

## Project Structure

```
archon/
├── main.py                           # Daemon entry point & OrchestratorDaemon
├── .env.example                      # Configuration template
├── pyproject.toml                    # Package metadata & dependencies
├── ai-orchestrator.service           # Systemd service unit
├── SKILLS_INDEX.md                   # Full 360-skill annotated index
│
├── src/
│   ├── config/
│   │   ├── settings.py               # Pydantic settings (env-driven)
│   │   └── logging_config.py         # Rotating file + console logging
│   │
│   ├── core/
│   │   ├── graph_manager.py          # Thread lifecycle, approval flow, recovery
│   │   ├── manager_planning.py       # ManagerPlanningService — Gemini planner
│   │   ├── llm_providers.py          # Provider chain, prompt building, generation
│   │   ├── final_review.py           # Gemini auditor (post-generation review)
│   │   ├── ai_scanner.py             # Health probe for all LLM providers
│   │   ├── retry_policy.py           # Exponential backoff + error classification
│   │   ├── approval_guard.py         # Idempotent approval validation
│   │   ├── event_bus.py              # Pub/sub system (EventBus)
│   │   ├── state_manager.py          # In-memory + JSON snapshot persistence
│   │   ├── project_manager.py        # Project CRUD
│   │   ├── context_builder.py        # Context summary for prompts
│   │   ├── memory_pipeline.py        # Post-review extract + consolidation scheduler
│   │   ├── consolidation_lock.py     # .consolidate-lock (mtime=last run) + rollback
│   │   ├── memory_paths.py           # Project-scoped memory root helpers
│   │   ├── memory_sessions.py        # Sprint snapshot activity scan (mtime-based)
│   │   ├── recovery.py               # Sprint recovery analysis
│   │   ├── scheduler.py              # Fair scheduling across projects
│   │   ├── state_transaction.py      # Transactional state updates
│   │   └── contracts.py              # Pydantic models (Event, ApprovalRequest…)
│   │
│   ├── graph/
│   │   ├── graph.py                  # LangGraph builder + SQLite checkpointer
│   │   ├── state.py                  # OrchestratorState (TypedDict, 60+ fields)
│   │   ├── edges.py                  # Conditional routing functions
│   │   └── nodes/
│   │       ├── planner.py            # Planning & approval gate
│   │       ├── dispatcher.py         # Worker assignment & queue management
│   │       ├── worker.py             # LLM file generation
│   │       ├── executor.py           # Project build execution
│   │       ├── validator.py          # Syntax + policy validation
│   │       └── reviewer.py           # Review & retry decisions
│   │
│   ├── storage/
│   │   ├── models.py                 # Pydantic models (Project, Sprint, FileRecord…)
│   │   └── repository.py             # Database CRUD layer
│   │
│   └── interfaces/
│       ├── cli/
│       │   ├── app.py                # Textual TUI application
│       │   ├── commands.py           # Command parser & executor
│       │   ├── state_view.py         # Output formatting
│       │   └── notifier.py           # Async event → TUI notifications
│       └── telegram/
│           └── bot.py                # python-telegram-bot handler
│
├── scripts/
│   ├── preflight.py                  # Pre-launch configuration validation
│   ├── check_connections.py          # LLM provider connectivity smoke test
│   ├── healthcheck.py                # System health probe
│   ├── smoke_fullstack.py            # End-to-end workflow test
│   └── load_simulation.py            # Concurrent project stress test
│
├── tests/
│   ├── test_cli_apply_command.py
│   └── test_openrouter_only_models.py
│
├── docs/
│   ├── MANAGER_PLANNING.md           # Planner integration deep-dive
│   ├── REAL_WORKER.md                # Worker provider setup guide
│   └── PHASE_ACCEPTANCE.md           # Phase completion criteria
│
├── data/                             # Runtime data (auto-created)
│   ├── orchestrator.db               # SQLite project database
│   ├── langgraph_checkpoints.sqlite  # Thread checkpoints
│   ├── daemon_status.json            # Live daemon heartbeat
│   └── ai-orchestrator.pid           # Daemon process ID
│
├── logs/                             # Rotating log files (auto-created)
│   └── orchestrator.log
│
├── projects/                         # Generated project outputs (auto-created)
│   └── <project-name>/
│       ├── src/, tests/, Dockerfile… # AI-generated files
│       └── .meta/context.md          # Execution context snapshot
│
└── skills/                           # 360 skill knowledge files
    └── <skill-name>/SKILL.md
```

---

## Key Design Principles

**1. Stateful, resumable execution**
Every graph transition is persisted to SQLite via LangGraph's checkpointer. Crash the daemon mid-sprint — `python main.py` + `/recover` brings it back exactly where it stopped.

**2. Approval-gated by design**
No file is generated without an explicit human approval. The gate is idempotent (duplicate approvals are rejected), time-bounded (15-minute expiry), and audit-logged.

**3. Multi-model fallback chain**
Workers try Ollama (free, local) → OpenRouter Primary → OpenRouter Secondary → Gemini stub. A single provider outage never blocks a sprint.

**4. Self-correcting loop**
Validator failures and runtime errors are fed back into the Worker prompt on the next cycle. The Reviewer enforces a maximum of 6 correction cycles before failing gracefully.

**5. File reservation system**
The Dispatcher atomically reserves files before generation. No two workers ever write the same file concurrently — a common race condition in naive multi-agent systems.

**6. Async-first**
Every component is built on `asyncio` + `httpx`. The EventBus decouples the LangGraph runtime from the CLI and Telegram interfaces without blocking either.

**7. Bilingual support**
The Planner understands Turkish and English natively. Execution-intent keywords (`uygula`, `apply`, `sprint baslat`, `implement`) are detected in both languages.

---

## Testing

```bash
# Recommended: venv (PEP 668 friendly)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Unit & integration tests
pytest

# LLM provider connectivity
python scripts/check_connections.py

# Full configuration validation
python scripts/preflight.py

# End-to-end workflow smoke test
python scripts/smoke_fullstack.py

# Concurrent load simulation
python scripts/load_simulation.py
```

---

## Deployment

### Systemd Service

```bash
# Copy and enable the service
sudo cp ai-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-orchestrator
sudo systemctl start ai-orchestrator

# View logs
journalctl -u ai-orchestrator -f
```

The service file expects:
- Working directory: `/home/user/caglarkc-agent`
- Virtual environment at `.venv/`
- `.env` file present in the working directory

### Health Monitoring

```bash
# Live daemon status
cat data/daemon_status.json

# Provider health (from inside TUI)
/scan
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `langgraph` | ≥1.0 | State machine orchestration |
| `langgraph-checkpoint-sqlite` | ≥2.0 | Thread persistence |
| `langchain-google-genai` | ≥2.0 | Gemini integration |
| `langchain-openai` | ≥0.3 | OpenRouter integration |
| `pydantic` / `pydantic-settings` | ≥2.7 | Data validation & settings |
| `textual` | ≥0.86 | Terminal UI |
| `python-telegram-bot` | ≥21.6 | Telegram interface |
| `httpx` | ≥0.27 | Async HTTP client |
| `aiosqlite` | ≥0.20 | Async SQLite access |
| `rich` | ≥13.7 | Console output formatting |

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

*ARCHON — because every great team needs an orchestrator.*
