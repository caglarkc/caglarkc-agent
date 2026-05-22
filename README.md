# ARCHON - AI Development Team Orchestrator

ARCHON is a Python-based, LangGraph-powered orchestration system for managing AI-assisted software development workflows. It turns a high-level project request into a structured plan, routes file-generation tasks through a stateful worker pipeline, validates generated artifacts, and keeps a human approval gate between planning and execution.

The project is designed as a local-first engineering assistant: a user can describe a software idea from a terminal UI or Telegram, review the generated plan, approve execution, and let the orchestrator coordinate planning, file generation, validation, review, persistence, and recovery.

## Problem And Goals

AI coding tools are useful, but larger tasks often need coordination: planning, file ownership, retries, validation, state recovery, and a reliable way for a human to approve work before files are generated. ARCHON addresses that coordination layer.

The core goals visible in this repository are:

- Convert conversational requirements into structured project plans.
- Keep execution approval-gated so worker generation does not start accidentally.
- Persist project, sprint, file, and decision state in SQLite.
- Resume or recover interrupted LangGraph threads through checkpointing.
- Route work through a deterministic graph: planner, dispatcher, worker, executor, validator, reviewer.
- Validate generated files with syntax checks, import checks, runtime checks, and policy checks.
- Provide local operations through a Textual CLI and optional Telegram bot interface.
- Maintain post-sprint memory extracts for future planning context.

## Key Features

- **Human-in-the-loop planning**: The planner can discuss requirements, produce a structured draft plan, and wait for explicit approval before execution.
- **LangGraph state machine**: The workflow is implemented as a resumable graph with conditional routing and SQLite checkpoints.
- **Project and sprint persistence**: Projects, sprints, file records, decisions, and worker failures are stored with `aiosqlite`.
- **File reservation and worker routing**: The dispatcher reserves files, respects dependencies, detects dependency cycles, and assigns work to idle workers.
- **Gemini-backed planning and generation**: Manager planning, worker generation, and final review use Gemini when configured. A heuristic planner fallback exists for planning failures.
- **Executor and validator loop**: Generated Python, JSON, HTML, CSS, and JavaScript artifacts are checked before review. Project-level `pytest` or `npm test` commands are run when the generated project contains the relevant config and tools are available.
- **Final project review**: A Gemini-based final audit can inspect generated files and execution results before approving a sprint.
- **Textual terminal UI**: A live terminal interface displays sprint status, events, approvals, and command input.
- **Telegram interface**: Optional bot integration mirrors the workflow from an authorized chat.
- **Provider health checks**: The codebase contains health probes for Gemini, Ollama, and OpenRouter. The active `/scan` command currently gathers Gemini status through `AIScanner.scan_all()`.
- **Operational tooling**: Scripts cover preflight checks, health checks, connection checks, smoke tests, backup/restore tests, phase checks, and load simulation.
- **Post-sprint memory pipeline**: Approved or failed sprints can write memory extracts and consolidate them into planner-facing Markdown under the generated project metadata folder.
- **Skill knowledge library**: The repository includes 360 `skills/*/SKILL.md` files plus `SKILLS_INDEX.md` for planner/coder guidance.

## Architecture

```text
User
  |
  | Textual CLI or Telegram
  v
EventBus
  |
  v
GraphManager
  |
  v
LangGraph workflow
  |
  +--> planner
  +--> dispatcher
  +--> worker
  +--> executor
  +--> validator
  +--> reviewer
  |
  v
SQLite repository + LangGraph checkpoint database
  |
  v
projects/<project-name>/ generated output and .meta state
```

### Workflow Nodes

1. **Planner**
   - Reads the user request and conversation history.
   - Uses `ManagerPlanningService` to build or refine a structured plan.
   - Detects execution intent in Turkish and English.
   - Emits approval requests before worker execution.

2. **Dispatcher**
   - Reads the worker queue and dependencies.
   - Detects dependency cycles.
   - Selects an idle worker based on failure counts and current load.
   - Reserves one target file before generation.

3. **Worker**
   - Builds a context-rich prompt for one assigned file.
   - Generates raw file content through the configured Gemini worker path.
   - Writes output into `projects/<project-name>/`.
   - Records worker success or failure in SQLite.

4. **Executor**
   - Runs targeted checks for generated artifacts.
   - Compiles Python files, parses JSON files, checks static frontend structure, verifies DOM references, and runs generated project tests when discoverable.
   - Uses a 20-second default timeout for individual checks.

5. **Validator**
   - Performs Python syntax and import checks.
   - Validates JSON parsing.
   - Applies policy checks for path traversal, prompt override text, forbidden filesystem paths, and leaked planner JSON in frontend artifacts.

6. **Reviewer**
   - Decides whether the sprint is approved, needs revision, or failed.
   - Requeues affected files when validation or final review finds issues.
   - Limits blocking review cycles.
   - Writes final sprint snapshots and schedules memory extraction.

## Tech Stack

- **Language**: Python 3.11+
- **Workflow orchestration**: LangGraph
- **LLM integration**: `langchain-google-genai`, `langchain-openai`, direct HTTP calls for provider probes
- **Primary active model path**: Gemini for manager planning, worker generation, and final review
- **Configuration**: Pydantic Settings from `.env`
- **Persistence**: SQLite through `aiosqlite`
- **Checkpointing**: `langgraph-checkpoint-sqlite`
- **CLI UI**: Textual and Rich
- **Telegram integration**: `python-telegram-bot`
- **Async IO**: `asyncio`, `httpx`, `aiofiles`
- **Testing**: pytest and pytest-asyncio
- **Service deployment**: systemd unit file

## Important Modules And Folders

```text
.
|-- main.py                         # Daemon entry point and service lifecycle
|-- pyproject.toml                  # Package metadata, dependencies, pytest config
|-- .env.example                    # Environment variable template
|-- ai-orchestrator.service         # systemd service unit
|-- RUNBOOK.md                      # Local CLI workflow notes
|-- docs/                           # Operations, deployment, planning, worker docs
|-- documents/                      # Integration notes and reference material
|-- scripts/                        # Preflight, health, smoke, load, phase checks
|-- skills/                         # 360 skill documents for planner/coder guidance
|-- SKILLS_INDEX.md                 # Annotated skill index
|-- src/
|   |-- config/                     # Settings and logging configuration
|   |-- core/                       # Planning, graph management, providers, memory, recovery
|   |-- graph/                      # LangGraph state, edges, and workflow nodes
|   |-- interfaces/cli/             # Textual CLI app, panels, commands, notifications
|   |-- interfaces/telegram/        # Telegram bot, handlers, notifier, views
|   `-- storage/                    # SQLite repository and Pydantic storage models
|-- tests/                          # Unit and integration tests
|-- data/                           # Runtime data and SQLite files, gitignored where needed
|-- logs/                           # Runtime logs, gitignored
`-- projects/                       # Generated project outputs, gitignored
```

## Configuration

Copy `.env.example` to `.env` and fill in the values required for your workflow.

```bash
cp .env.example .env
```

Environment variables discoverable from `.env.example` and `src/config/settings.py`:

| Variable | Purpose |
|---|---|
| `APP_NAME` | Application name used in status output. |
| `APP_ENV` | Runtime environment label. |
| `LOG_LEVEL` | Logging level. |
| `LOG_DIR` | Log output directory. |
| `LOG_FILE_NAME` | Main log filename. |
| `LOG_MAX_BYTES` | Rotating log file size. |
| `LOG_BACKUP_COUNT` | Number of rotated log backups. |
| `DATA_DIR` | Runtime data directory. |
| `PROJECTS_ROOT` | Directory where generated projects are written. |
| `SQLITE_DB_PATH` | Main application SQLite database. |
| `GRAPH_CHECKPOINT_PATH` | LangGraph checkpoint SQLite database. |
| `GRAPH_THREAD_PREFIX` | Prefix used for graph thread naming. |
| `HTTP_TIMEOUT_SECONDS` | HTTP timeout used by model and provider calls. |
| `CONTEXT_MAX_DECISIONS` | Maximum number of decisions included in context. |
| `CONTEXT_OUTPUT_FILE` | Project metadata context filename. |
| `GEMINI_API_KEY` | Gemini API key for planning, generation, scanning, and review. |
| `GEMINI_BASE_URL` | Gemini API base URL. |
| `GEMINI_MODEL` | Gemini model used by workers and fallback paths. |
| `MANAGER_USE_GEMINI` | Enables Gemini-backed manager planning. |
| `MANAGER_MODEL` | Gemini model used by manager planning and final review. |
| `MANAGER_MAX_HISTORY_TURNS` | Conversation history limit for planning. |
| `USE_LEGACY_PLANNER` | Legacy planner switch. |
| `OLLAMA_BASE_URL` | Ollama endpoint used by preflight and probe code. |
| `OLLAMA_MODEL` | Ollama model name expected by preflight and probe code. |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL used by probe code. |
| `OPENROUTER_MODEL` | Primary OpenRouter model configured for probes/settings. |
| `OPENROUTER_MODEL_SECONDARY` | Secondary OpenRouter model configured for probes/settings. |
| `OPENROUTER_API_KEY_PRIMARY` | Primary OpenRouter key. |
| `OPENROUTER_API_KEY_SECONDARY` | Secondary OpenRouter key. |
| `WORKER_USE_STUB` | Uses deterministic stub content instead of real worker generation. |
| `FINAL_REVIEW_ENABLED` | Enables final model review after validation. |
| `FINAL_REVIEW_TIMEOUT_SECONDS` | Timeout for final review requests. |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token. |
| `TELEGRAM_CHAT_ID` | Authorized Telegram chat ID. |
| `MEMORY_AUTO_ENABLED` | Enables post-sprint memory behavior in settings. |
| `MEMORY_CONSOLIDATION_ENABLED` | Enables memory consolidation. |
| `MEMORY_RELATIVE_DIR` | Project-relative memory metadata folder. |
| `MEMORY_PLANNER_SUMMARY_FILE` | Consolidated planner memory filename. |
| `MEMORY_MIN_HOURS_BETWEEN_RUNS` | Time gate for memory consolidation. |
| `MEMORY_MIN_SESSIONS` | Session activity gate for memory consolidation. |
| `MEMORY_SESSION_SCAN_INTERVAL_SECONDS` | Throttle for scanning sprint snapshots. |
| `MEMORY_LOCK_HOLDER_STALE_SECONDS` | Stale lock threshold. |
| `MEMORY_CONSOLIDATION_USE_LLM` | Optionally uses Gemini for consolidation. |
| `MEMORY_CONSOLIDATION_MAX_INPUT_CHARS` | Maximum consolidation input size. |

### Configuration Notes

- `GEMINI_API_KEY` is required for the active Gemini-backed planner, worker, scanner, and final review paths.
- `scripts/preflight.py` currently treats `OLLAMA_BASE_URL` and `OLLAMA_MODEL` as required daemon/runtime settings and checks the configured Ollama model.
- OpenRouter settings are present and probe methods exist in `AIScanner`, but the active worker fallback chain in `src/core/llm_providers.py` is Gemini-only in the current code.
- Telegram is optional. If used, both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` should be configured together.

## Installation

### Prerequisites

- Python 3.11 or newer
- A Gemini API key for real planning/generation/review
- Optional Ollama setup if you want `preflight` provider checks to pass with local model validation
- Optional Telegram bot token and chat ID for remote chat control

### Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` before running the daemon or checks.

## Running The Application

### Recommended Local CLI Mode

```bash
./.venv/bin/python main.py --cli --no-telegram
```

This starts the Textual CLI and disables Telegram for local testing.

### Daemon Without Telegram

```bash
./.venv/bin/python main.py --no-telegram
```

### Daemon With CLI And Telegram

```bash
./.venv/bin/python main.py --cli
```

### Headless Daemon

```bash
./.venv/bin/python main.py
```

Telegram starts only when `TELEGRAM_BOT_TOKEN` is configured and Telegram is not disabled.

## CLI Workflow

Start the CLI:

```bash
./.venv/bin/python main.py --cli --no-telegram
```

Inside the CLI:

```text
/new My Project
/r Build a small FastAPI service with CRUD endpoints and tests.
/plan
/approve
/status
```

Useful commands implemented in `src/interfaces/cli/commands.py`:

```text
/task <text>
/new <project name>
/resume [project_id or project name]
/r <message>
/plan [project_id or project name]
/changePlan <change request>
/start [project_id or project name]
/apply [optional note]
/status
/approve [approval_id]
/reject [approval_id] [reason]
/cancel [approval_id] [reason]
/close [reason]
/recover [project_id or project name]
/projects
/history <project>
/project use <id or project name>
/scan
/help
```

## Generated Project Output

Generated projects are written under:

```text
projects/<project-name>/
```

The project manager also creates metadata folders such as:

```text
projects/<project-name>/.meta/
projects/<project-name>/.meta/sprints/
projects/<project-name>/.meta/archived/
projects/<project-name>/.meta/memory/
projects/<project-name>/.meta/memory/extracts/
```

Examples of generated metadata include `plan.json`, sprint snapshots, context output, memory extracts, and consolidated planner memory.

## Testing And Quality Checks

Install development dependencies first:

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

Run operational checks:

```bash
./.venv/bin/python -m scripts.preflight
./.venv/bin/python -m scripts.healthcheck
./.venv/bin/python -m scripts.check_connections
./.venv/bin/python -m scripts.smoke_fullstack
./.venv/bin/python -m scripts.backup_restore_test
./.venv/bin/python -m scripts.load_simulation
```

Additional phase-check scripts are available under `scripts/`.

## Deployment

The repository includes a systemd unit:

```text
ai-orchestrator.service
```

The current service file is configured for this local path:

```text
/home/caglarkc/Desktop/Github/caglarkc-agent
```

Before using it on another machine, update:

- `User`
- `WorkingDirectory`
- `EnvironmentFile`
- `ExecStart`
- `StandardOutput`
- `StandardError`

Typical systemd flow:

```bash
sudo cp ai-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-orchestrator
sudo systemctl start ai-orchestrator
journalctl -u ai-orchestrator -f
```

Operational documentation is available in:

- `docs/OPERATIONS.md`
- `docs/DEPLOYMENT_CHECKLIST.md`
- `docs/INCIDENT_RUNBOOK.md`
- `RUNBOOK.md`

## Security And Reliability Notes

The codebase includes several guardrails that are important for an AI code-generation orchestrator:

- **Approval gate**: Plans require explicit approval before execution.
- **Idempotency protection**: Approval handling rejects duplicate approval attempts.
- **Path safety checks**: Worker, executor, validator, and final review file reading paths guard against traversal outside the project root.
- **Prompt-injection policy checks**: Validator flags generated artifacts containing phrases such as `ignore previous instructions` or `prompt override`.
- **Forbidden path checks**: Validator flags generated content containing `/etc/` or home-directory path usage.
- **Frontend artifact checks**: Executor validates static HTML structure, CSS brace balance, JavaScript syntax when Node is available, DOM selector consistency, and missing local CSS assets.
- **Timeouts**: HTTP/model calls and executor checks use configured or fixed timeouts to avoid indefinite blocking.
- **Retry and failure records**: Worker failures are classified, retried when appropriate, and stored with recommendations.
- **State recovery**: LangGraph checkpoints and JSON state snapshots support recovery after interruption.
- **Memory consolidation locks**: The memory pipeline uses time gates, session gates, and lock files to avoid repeated or concurrent consolidation.

## Current Limitations

- No screenshot or image assets were found in the repository.
- No `LICENSE` file was found in the project root.
- No Dockerfile or container deployment configuration was found.
- OpenRouter and Ollama settings/probe helpers exist, but active worker generation in the inspected code is Gemini-only.
- `AIScanner.scan_all()` currently returns only the Gemini scan result, even though individual Ollama and OpenRouter scan methods exist.
- `scripts/preflight.py` requires a configured Ollama model, while the active worker generation path uses Gemini.
- Several docs are written in Turkish; the README is intentionally written in English for international portfolio use.

## Future Improvements

Potential next steps based on the repository's docs and current implementation:

- Expand `AIScanner.scan_all()` to include Ollama and OpenRouter when configured.
- Align preflight requirements with the active provider strategy, or clearly separate optional local-provider checks from required runtime checks.
- Add true multi-provider worker fallback if Ollama/OpenRouter should be part of execution, not only settings/probes.
- Add a Dockerfile or compose setup if container deployment is desired.
- Add screenshots or conceptual architecture images for portfolio presentation.
- Add a root `LICENSE` file if the project is intended for public reuse.
- Add coverage reporting and CI configuration for automated test visibility.
- Continue developing worker tool-calling support if workers should inspect and execute generated code directly.

## Repository Status Summary

ARCHON is best described as a local, approval-gated AI software development orchestrator with a LangGraph execution core, SQLite persistence, Textual and Telegram interfaces, Gemini-backed planning/generation/review, validation and recovery tooling, and an extensive skill-document library.
