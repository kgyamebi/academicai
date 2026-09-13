# Billing Runbook — AcademicCheck AI

Live PSP keys in this environment: **absent** (`ops/cert_payment_keys.json`). This runbook is for when keys exist.

## Checkout 502/503

1. Circuit may be open (`academiccheck_circuit` / `/api/metrics`).
2. Missing keys → 503 by design. Do not “force” a paid plan in the database.
3. User retry is safe: failed/cancelled payment rows reuse the idempotency key.

## Duplicate webhook

1. `WebhookEvent` uniqueness. Replays must not double-grant (pytest).
2. Unmatched actionable webhook → 503, `processed_at` null — provider will retry. Find the payment row; do not mark processed by hand.

## Refund / partial refund

1. Apply only through the billing service (ledger clawback). Do not decrement `credits.remaining` in SQL.
2. Live provider refund dashboard must match ledger; **live refund unrun here**.

## Double subscription

1. Second successful subscription cancels the previous active one (pytest).
2. If two `active` rows appear: incident — freeze checkout, restore from backup if ledger is inconsistent.

## Alerts (specified, not paged)

Payment apply failures after retry; webhook signature failures > 20 / 5 min (`docs/ALERTS_AND_SLOS.md`). PagerDuty is **not** wired.
