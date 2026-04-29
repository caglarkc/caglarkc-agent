# Phase 5 Acceptance

## CLI Screen Structure

- left panel: sprint status, sprint type, file registry
- right panel: live event log ring buffer
- bottom panel: active approval id, type, timeout, stale/expired visibility
- command input: deterministic slash-command interface

## Command Dictionary

- `/task <metin>`
- `/status`
- `/approve [approval_id]`
- `/reject [approval_id] [reason]`
- `/cancel [approval_id] [reason]`
- `/help`

## Approval Event Flow

- CLI resolves the active approval when `approval_id` is omitted
- stale or expired approvals are rejected locally without mutating state
- approval events are emitted through EventBus with contract-first envelopes
- duplicate follow-up approvals remain safe because GraphManager and ApprovalGuard keep idempotency semantics

## Validation Coverage

- app bootstrap and panel render
- EventBus to UI state sync
- `/task` publishing
- `/approve` active approval flow
- stale approval safety
- `/status` deterministic summary
- heartbeat and stalled visibility

## Phase 6 Handoff Guarantees

- Telegram can reuse the same approval event contract and notifier model
- CLI already proves that approval/review orchestration works without blocking console input
