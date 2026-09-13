# Ledger Architecture — AcademicCheck AI

Date: 2026-09-09  

## Layers

| Layer | Tables | Mutability |
| --- | --- | --- |
| Payments | `payments`, `payment_transactions` | Payment status advances; txn rows append with unique `provider_event_id` |
| Credits | `credits` (wallet), `credit_transactions` | Wallet mutable; txn amounts immutable; status may advance reserved→consumed/refunded |
| Subscriptions | `subscriptions` | Status via FSM; period fields update on renew |

## Credit grant audit fields

Each grant writes `CreditTransaction` with `operation`, `amount`, `status=available`, and `notes` including `previous=` / `new=` balances.

## Integrity rule

`assert_wallet_integrity` runs **pre** and **post** `grant_credits`. Drift → HTTP 409 + `billing.ledger_drift` metric. No silent repair.

## Gaps (honest)

- Not a pure append-only accounting ledger (wallet exists).
- No DB trigger preventing raw SQL wallet edits.
- PaymentTransaction does not store a separate amount column (amount on Payment + payload).

**Architecture: PASS for SaaS dual-write with fail-closed drift on grant.**  
**FAIL** as immutable banking core ledger claim.
