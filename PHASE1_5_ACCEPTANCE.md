# Phase 1.5 Acceptance

Phase 1.5 codifies the orchestration contract that Phase 2 must build on.

## Implemented Guarantees

- typed event envelope contract with validation helpers
- approval request and decision contract models
- stale approval detection
- idempotent approval handling
- retry classification with deterministic backoff+jitter
- per-project atomic state transaction with rollback
- contract-aware GraphManager approval bridge skeleton

## Validation Coverage

`scripts/check_phase1_5.py` verifies:
- contract model validation
- stale approval rejection without state mutation
- duplicate idempotency decision no-op behavior
- retry classification and backoff generation
- state transaction rollback on exception
- GraphManager accepted/no-op/stale routing behavior

## Phase 2 Handoff

Phase 2 can assume:
- approval events have a stable envelope format
- duplicate or stale approval events do not resume the graph
- retryable vs non-retryable failures are classified consistently
- project-scoped in-memory state mutations can be rolled back safely
