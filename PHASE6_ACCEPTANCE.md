# Phase 6 Acceptance

## Telegram Command Dictionary

- `/task <metin>`
- `/status`
- `/cancel [approval_id] [reason]`
- `/help`

## Approval Keyboard Flow

- `plan.approval_needed` creates an inline keyboard with approve / reject / cancel options
- callback payload carries `approval_id`, `decision`, and deterministic `idempotency_key`
- stale approvals are rejected without state mutation
- duplicate/processed callbacks return a clear user message

## Authorization Security

- only `TELEGRAM_CHAT_ID` is authorized
- unauthorized commands are ignored and warned
- unauthorized callback queries are blocked the same way

## Validation Coverage

- bot bootstrap and handler registration
- authorized vs unauthorized command handling
- `/task` event publishing
- inline approval keyboard generation
- callback approve/reject/cancel event publishing
- stale callback safety
- deterministic `/status` rendering
- notifier flow for sprint/stalled/error events

## Phase 7 Handoff Guarantees

- Telegram now uses the same approval and orchestration contract as CLI
- a daemon runner can keep the bot online without changing approval semantics
