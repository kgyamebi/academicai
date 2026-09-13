# Financial Integrity Certification — AcademicCheck AI

Date: 2026-09-09  

## Score (honest)

| Category | Score | Gate | Pass? |
| --- | ---: | ---: | --- |
| Billing | **94** | 99 | **No** |

Engineering this pass (prior FSM / webhook freshness / grant-time drift fail-closed, plus extended dunning / proration / disputes / currency / cross-processor / chaos / FSM fuzz / audit trail) is **code-complete and pytest-proven**. Score stays **94** because live PSP (HAL-01–04) still caps the category below 95. Do not read 94 as live money certification.

## Mandatory rules

| Rule | Sandbox | Live |
| --- | --- | --- |
| Critical billing failures | None found in pytest | UNPROVEN |
| Double charges | Not observed (incl. dunning retry race) | UNPROVEN |
| Double credits | Not observed (incl. cross-processor logical id) | UNPROVEN |
| Ledger corruption | Detected + blocked on grant; audit chain + append-only triggers | UNPROVEN |
| Missing transactions | Reconcile flags; `charge.unknown` on timeout | Snapshot only |
| Unvalidated webhooks | Rejected | UNPROVEN |
| Dunning / proration / disputes | Pytest-proven (sandbox shapes) | UNPROVEN |

## Evidence this pass

- `tests/test_billing_critical.py` + sandbox + reconcile: previously **56**; this pass regression-checked critical + sandbox + reconcile (no new live money).
- `tests/test_billing_integrity_fsm.py` + critical subset: **11 passed** (FSM, stale webhook, drift 409, refund clawback, second sub, invoice renew) — not re-certified as new work; still green.
- **New (2026-09-09):** eight extended files **35 passed** — see `docs/BILLING_EXTENDED_CERTIFICATION.md` and `ops/cert_billing_extended.json`.
- Mutation kill-proof: `ops/cert_billing_mutation.json` (`killed: true`).

## Newly covered (sandbox only)

Dunning (3-attempt cancel, in-place recover, retry race), proration (day 17/30 exact cents, deferred downgrade, same-month resubscribe 409), disputes (Stripe / Paystack / Flutterwave sandbox webhooks), Decimal display FX (incl. JPY zero-decimal), cross-processor `logical_purchase_id`, webhook crash/timeout/burst chaos, FSM pair-fuzz + mutation, hash-chained append-only audit.

## Still blocked on live money (unchanged)

1. HAL-01 live ~$1 **success**  
2. HAL-02 live **decline**  
3. HAL-03 live Dashboard **refund**  
4. HAL-04 provider cancel on delete  

Harness: `docs/LIVE_TRANSACTION_VERIFICATION.md`.

## Launch recommendation

**NO-GO** for financial-grade production certification until live drills PASS.

Sandbox billing now also covers dunning, proration, chargebacks, FX rounding, cross-processor de-dup, chaos, fuzz, and audit immutability. That is **not** live money certification.
