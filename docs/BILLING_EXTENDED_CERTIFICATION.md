# Billing Extended Certification — AcademicCheck AI

Date: 2026-09-09  
Scope: dunning, proration, disputes, currency precision, cross-processor de-dup, chaos, FSM fuzz/mutation, immutable audit trail.  
Processors: **sandbox / local simulation only**. No live money.

## Score (honest)

| Category | Score | Gate | Pass? |
| --- | ---: | ---: | --- |
| Billing | **94** | 99 | **No** |

This pass adds logic coverage only. Score stays **94** because the live `$1` success / decline / refund harness (HAL-01–03) is still unrun. Do not read any row below as live-PSP certification.

## New evidence

| Step | Result | Artifact |
| --- | --- | --- |
| 1 Dunning | **PASS** | `backend/tests/test_billing_dunning.py` |
| 2 Proration | **PASS** | `backend/tests/test_billing_proration.py` |
| 3 Disputes | **PASS** | `backend/tests/test_billing_disputes.py` |
| 4 Currency | **PASS** | `backend/tests/test_billing_currency.py` |
| 5 Cross-processor | **PASS** | `backend/tests/test_billing_cross_processor.py` |
| 6 Chaos | **PASS** | `backend/tests/test_billing_chaos.py` |
| 7 Fuzz + mutation | **PASS** | `backend/tests/test_billing_fsm_fuzz.py`, `ops/cert_billing_mutation.json` |
| 8 Audit trail | **PASS** | `backend/tests/test_billing_audit.py` |

Suite run (2026-09-09, `py -3.14`): **35 passed** on the eight new files. Combined with previously certified integrity + critical: **59 passed**. Sandbox + reconcile regression: **39 passed**. Mutation script: **killed true**.

Machine-readable: `ops/cert_billing_extended.json`.

---

### 1. Dunning / failed-payment recovery

Policy: **3 failed renewals then cancel**. Each failure moves `active → past_due` (or stays `past_due`) and increments `dunning_attempts`. Attempt 3 cancels. A later success on the same plan **recovers the same row** (`past_due → active`) instead of inserting a second subscription.

- Automatic retry uses idempotency key `dunning:{subscription_id}:{attempts}` so two concurrent retries share one payment row.
- Customer payment-method update mid-dunning: one retry payment → success → recovered, attempts reset to 0.
- Race: two success events on the same retry payment produce **one** `payment.successful` transaction and **one** active subscription.

### 2. Proration and plan changes

Integer cents only (`Decimal` `ROUND_HALF_EVEN`). Cycle example is **day 17 of 30** (13 remaining days), not a round split.

| Change | Policy | Proven |
| --- | --- | --- |
| Student $1.99 → Pro $3.99 on day 17 | Charge unused_new − unused_old = **87 cents** (173 − 86) | exact |
| Pro → Student on day 17 | **Deferred** to next cycle; `pending_plan_id` stored; **0** immediate credit | exact |
| Cancel then resubscribe same `YYYYMM` key | **409** — monthly idempotency key already successful | exact |

### 3. Disputes / chargebacks

Sandbox-shaped webhooks (no live Dashboard dispute objects):

| Processor | Open | Resolve |
| --- | --- | --- |
| Stripe | `charge.dispute.created` | `charge.dispute.closed` (`won` / `lost`) |
| Paystack | `charge.dispute.create` | `charge.dispute.resolve` |
| Flutterwave | `dispute.created` | `dispute.resolved` |

Policy: open sets payment `disputed` and subscription `suspended`. Credits are **not** clawed back until the dispute is **lost**. Won restores `successful` + `active`. Lost applies refund semantics and cancels.

### 4. Currency and rounding

Ledger unit remains **USD cents**. Display conversion uses `Decimal`, never binary floats.

- GHS: 299 USD cents × 15.4 → **46.05** (4605 pesewas). Ledger still 299.
- JPY / KRW / VND: zero-decimal display; 199 × 150 JPY → **298** yen (`ROUND_HALF_EVEN` on 298.5).
- Charged (USD cents), shown (`amount_decimal` / `minor_units`), and recorded (`payments.amount_cents`) are compared in tests.

Non-USD PSP charge formulas are display/catalog helpers only and are **not** live-certified.

### 5. Cross-processor consistency

`raw_payload.logical_purchase_id` (defaults to the checkout idempotency key). If a second processor reports success for the same logical id, the payment is recorded successful but **entitlements are not granted twice** (no second credit pack, no second subscription).

### 6. Chaos / failure injection

| Injection | Outcome |
| --- | --- |
| DB write of success + webhook row, crash before `processed_at` | Replay no-ops entitlements; one success txn |
| Ack (`processed_at` set) before apply | Replay skipped; reconcile flags gap vs provider snapshot |
| Processor timeout during charge | Payment stays `pending`; `charge.unknown` txn; reconcile `charge_unknown`; **never** assumed success or failure |
| Hours-later burst of shuffled duplicates | One logical credit grant; webhook dedup holds |

### 7. FSM fuzz and mutation

- Every status pair plus garbage events: illegal transitions **409**, unknown **400**, 200 random walks never apply a forbidden edge.
- Mutation kill-proof (`ops/cert_billing_mutation.py`): injecting `cancelled → past_due` into the allow-list would make the existing 409 assertion fail; injecting `MAX_ATTEMPTS=99` would make exhaustion-cancel fail. Both mutants **killed**. Restored code still rejects.

This is an in-process mutmut equivalent on FSM + dunning policy, not a full mutmut install against every billing line.

### 8. Immutable audit trail

`financial_audit_entries`: SHA-256 hash chain (`prev_hash` → `entry_hash`). Success / fail / refund / dispute / `charge.unknown` append. SQLite and Postgres triggers reject **UPDATE** and **DELETE**. Tampering `payload_hash` fails `verify_chain`. Alembic `012_billing_dunning_audit.py` adds columns + table + triggers for cert Postgres.

---

## Still blocked on live money (unchanged)

The `$1` harness in `docs/LIVE_TRANSACTION_VERIFICATION.md` is the only remaining billing-logic gap that cannot be closed locally:

1. **HAL-01** — live success (~$1) on a real processor  
2. **HAL-02** — live decline  
3. **HAL-03** — live Dashboard refund of #1  
4. **HAL-04** — provider-side cancel on account delete (still human)

Everything in this document is sandbox/test-mode or local simulation. **Launch remains NO-GO.**
