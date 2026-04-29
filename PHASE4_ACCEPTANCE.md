# Phase 4 Acceptance

## Implemented Rules

- reviewer now produces deterministic `approved | revision | fail` outcomes
- revision loops only requeue validator-failing files and stop after 3 cycles
- validator enforces python syntax, import existence, json parsing, path traversal, and prompt/path override guards
- context builder preserves Tier1 decisions/contracts, includes Tier2 recent sprint summaries, and trims deterministically within budget
- reviewer decisions are persisted to `Decision` storage and fed back into future context
- dispatcher heartbeat tracking can emit `system.stalled` after prolonged silence with grace for active assignments

## Validation Coverage

- reviewer revision loop targets only broken files
- max review cycle fail behavior
- validator path/json/import/policy checks
- context tiering plus deterministic trimming
- decision logging feedback into context
- heartbeat to stalled event flow

## Phase 5 Handoff Guarantees

- once CLI/Telegram interfaces are added, review and approval outcomes will remain deterministic
- validator issue format is stable enough for user-facing reporting
- context assembly keeps critical decisions intact under budget pressure
