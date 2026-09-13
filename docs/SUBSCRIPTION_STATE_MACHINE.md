# Subscription State Machine — AcademicCheck AI

Date: 2026-09-09  
Module: `backend/app/services/subscription_fsm.py`

## States

`trialing` · `active` · `past_due` · `suspended` · `cancelled` · `expired`

## Allowed transitions

| From | To |
| --- | --- |
| trialing | active, past_due, cancelled, expired, suspended |
| active | past_due, cancelled, expired, suspended |
| past_due | active, cancelled, suspended, expired |
| suspended | active, cancelled, expired |
| cancelled | active (reopen; usual path is new row) |
| expired | active |

Illegal edges → HTTP 409.

## Wired paths

- New paid sub: prior `active` → `cancelled`; new row `active`
- Payment failed with `subscription_id` → `past_due`
- Full subscription refund → active (provider match) → `cancelled`

## Product notes

- User cancel API sets `cancel_at_period_end` without leaving `active` (access until period end) — not an FSM edge.
- `refunded` is a **payment** state, not a subscription status.

Tests: `test_billing_integrity_fsm.py`.
