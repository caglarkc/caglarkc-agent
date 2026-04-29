# Orchestration Contract v1

Phase 1.5 defines the minimum orchestration contract that Phase 2 must honor.
This document is the source of truth for IDs, event envelopes, approvals, retry
behavior, and atomic state transitions.

Planning-first manager mode also emits advisory events before approval:
- `manager.reply`
- `plan.draft_updated`

## 1. ID Schema

All IDs are opaque strings. UUID4 is the default generator unless an external
system already owns the value.

| Field | Scope | Notes |
| --- | --- | --- |
| `project_id` | Project | Stable for the full project lifetime |
| `thread_id` | LangGraph thread | Stable for a resumable graph execution |
| `sprint_id` | Sprint | Stable for one sprint planning/review cycle |
| `task_id` | Dispatch assignment | Unique per work item |
| `approval_id` | Approval request | Unique per pending approval gate |
| `event_id` | Event envelope | Unique per emitted event |

## 2. Event Envelope Standard

Each event must be wrapped in `EventEnvelope`.

Required fields:
- `event_id`
- `event_type`
- `version` (`v1` by default)
- `timestamp` (ISO8601 UTC or offset-aware)
- `payload`

Contextual fields:
- `project_id`
- `thread_id`
- `sprint_id`
- `correlation_id`
- `idempotency_key`

Rules:
- `event_type` cannot be empty
- `timestamp` must be valid ISO8601
- `idempotency_key` is required for approval decisions
- `correlation_id` should point to the initiating workflow when available

## 3. Approval Contract

### Approval Event Types

- `plan.approval_needed`
- `plan.approved`
- `plan.rejected`
- `plan.cancelled`

### Approval Request Fields

- `approval_id`
- `project_id`
- `thread_id`
- `approval_type`
- `requested_at`
- `expires_at`
- `status`

Optional:
- `sprint_id`
- `reason`
- `metadata`

### Timeout Rule

- Default timeout is 15 minutes
- Once `expires_at` is in the past, the approval becomes stale
- Stale approvals cannot resume, reject, or cancel graph execution

### Stale Approval Rule

A decision is stale when any of the following is true:
- `approval_id` is unknown
- request status is no longer `pending`
- request timed out
- request thread/sprint no longer matches the active request

Result:
- no state mutation
- no graph resume/reject/cancel call
- explicit `stale` result returned

### Idempotency Rule

- Approval decisions must carry `idempotency_key`
- Repeated use of the same `idempotency_key` for the same approval is a no-op
- No duplicate state mutation
- No duplicate graph resume/reject/cancel call

## 4. Decision Matrix

| Incoming Decision | Request State | Result | State Transition | Graph Action |
| --- | --- | --- | --- | --- |
| `plan.approved` | pending + active | accepted | `pending -> approved` | resume allowed |
| `plan.rejected` | pending + active | rejected | `pending -> rejected` | reject/stop allowed |
| `plan.cancelled` | pending + active | cancelled | `pending -> cancelled` | cancel allowed |
| any decision | expired | stale | none | none |
| any decision | unknown approval | stale | none | none |
| repeated idempotency key | already handled | no-op | none | none |
| decision after terminal status | approved/rejected/cancelled/expired | stale | none | none |

## 5. Error Classes and Retry Matrix

### Retryable

- provider timeout
- transient network failure
- HTTP 429
- temporary HTTP 5xx provider errors

### Non-Retryable

- invalid or missing config
- schema validation failure
- policy violation
- HTTP 401 / 403
- malformed payload

## 6. Atomic State Update Pattern

Project state mutations should use `StateTransaction`.

Pattern:
1. acquire the project-specific lock
2. take a rollback snapshot
3. mutate the project state
4. commit on success
5. rollback to the snapshot on exception

Guarantees:
- project A does not block project B
- stale/idempotent approvals do not mutate state
- failed handlers restore the previous in-memory state
