# Live transaction verification — AcademicCheck AI

Date: 2026-09-07  
Status: **AWAITING HUMAN OPERATOR** — harness is ready; **no real charges were executed in this environment**.

Scripts **never** click Pay, confirm a PaymentIntent, or call refund APIs.  
They only (1) pre-check config, (2) prepare a labeled pending `$0.50–$1` Checkout for you to open, and (3) auto-verify ledger/webhooks after you finish.

## Certification boundary

| Layer | State |
| --- | --- |
| Sandbox / mock webhook logic | **Verified** — see `docs/BILLING_SANDBOX_VERIFICATION.md` |
| Live spot-check harness (preflight / prepare / verify) | **Ready** |
| Live success + decline + refund with real money | **PENDING human** |
| Multi-currency / multi-region live | **Unverified** (default harness = USD, single provider) |
| Processor fee line-items in-app | **N/A** — fees live in PSP dashboard; ledger stores customer charge only |

Target gate language after you finish: **sandbox + live spot-check verified** (one currency/provider unless you repeat the drill).

---

## Minimal real-money test set

| # | Scenario | Human action (required) | Auto-verify expects |
| --- | ---: | --- | --- |
| 1 | Successful small charge | Open `checkout_url`, pay with a real card (~$1) | `successful`, 1 success txn, webhook processed once, credits +1, amount exact |
| 2 | Intentional decline | Open decline checkout; use a card that declines (see below) | `failed`/`cancelled`, failure txn, no credit grant, webhook processed |
| 3 | Full refund of #1 | In **PSP Dashboard**, fully refund charge #1 | `refunded`, 1 refund txn, credits clawed back to pre-#1 baseline |

Default amount: **100 cents ($1.00)** via `LIVE_HARNESS_AMOUNT_CENTS` (allowed band 50–100).

### Safe decline guidance (live vs test)

| Mode | How to decline safely |
| --- | --- |
| **Stripe live** (`sk_live_`) | No magic decline PANs. Use a real card the issuer declines, **or** abandon Checkout until `checkout.session.expired` / cancel (verifier accepts `failed` **or** `cancelled`). |
| **Stripe test** (only if `LIVE_BILLING_ALLOW_TEST_KEYS=1`) | Use Stripe test decline PAN `4000000000000002` (see Stripe testing docs). |
| **Paystack / Flutterwave live** | Use an issuer-declined card or abandon; test PANs are for test mode only. |

---

## HUMAN OPERATOR — exact sequence

Do **not** skip preflight. Do **not** start scenario N+1 until scenario N verify = **PASS**. On **FAIL**, stop, fix, prepare a **fresh** session — do not reuse a corrupted payment.

### 0. Arm environment

```bash
export LIVE_BILLING_HARNESS=1
export LIVE_BILLING_PROVIDER=stripe          # or paystack / flutterwave
export LIVE_BILLING_USER_EMAIL='you@yourdomain.com'  # existing non-guest account
export LIVE_HARNESS_AMOUNT_CENTS=100
export LIVE_HARNESS_CURRENCY=USD
# Only if deliberately using test keys instead of live:
# export LIVE_BILLING_ALLOW_TEST_KEYS=1
```

Ensure live API keys + webhook secrets are loaded in the running API env, and the public webhook URL is registered in the PSP Dashboard.

### 1. Pre-flight (script — no money)

```bash
py -3.14 ops/live_billing_preflight.py
# Expect verdict PASS → ops/cert_live_billing_preflight.json
```

### 2. Scenario A — success

```bash
py -3.14 ops/live_billing_prepare.py --scenario success
# Opens nothing itself. Prints checkout_url + session path under ops/live_billing_sessions/
```

**HUMAN:** Open `checkout_url` in a browser and **complete a real payment**.  
Scripts do **not** automate this step.

```bash
py -3.14 ops/live_billing_verify.py --session ops/live_billing_sessions/success-STAMP.json \
  --out ops/cert_live_billing_verify_success.json
# Must print verdict PASS before continuing
```

| Field | Result |
| --- | --- |
| Verdict | **PENDING** |
| Evidence | `_pending_` (`cert_live_billing_verify_success.json`) |
| Ledger snapshot | `_pending_` |
| Webhook | `_pending_` |
| Amount reconciliation | `_pending_` (customer charge vs `Payment.amount_cents`) |

### 3. Scenario B — decline

```bash
py -3.14 ops/live_billing_prepare.py --scenario decline
```

**HUMAN:** Open the new `checkout_url` and **cause a real decline** (or abandon to expiry/cancel).  
Scripts do **not** automate this step.

```bash
py -3.14 ops/live_billing_verify.py --session ops/live_billing_sessions/decline-STAMP.json \
  --out ops/cert_live_billing_verify_decline.json
```

| Field | Result |
| --- | --- |
| Verdict | **PENDING** |
| Evidence | `_pending_` |

### 4. Scenario C — refund of success

```bash
py -3.14 ops/live_billing_prepare.py --scenario refund \
  --from-session ops/live_billing_sessions/success-STAMP.json
```

**HUMAN:** In the Stripe/Paystack/Flutterwave **Dashboard**, fully refund the successful harness charge.  
Scripts do **not** call refund APIs.

```bash
py -3.14 ops/live_billing_verify.py --session ops/live_billing_sessions/refund-STAMP.json \
  --out ops/cert_live_billing_verify_refund.json
```

| Field | Result |
| --- | --- |
| Verdict | **PENDING** |
| Credits restored to pre-success baseline | **PENDING** |

### 5. Accounting cleanup (human)

- Mark these Dashboard charges as **internal live harness / QA** in your books.
- Confirm the refund fully reversed the customer charge (PSP) and that verify PASS shows ledger `refunded` + credit clawback.
- `unset LIVE_BILLING_HARNESS LIVE_BILLING_USER_EMAIL`

---

## Script inventory

| Script | Moves money? | Role |
| --- | --- | --- |
| `ops/live_billing_preflight.py` | **No** | Keys, live/test mode, DB indexes, API + webhook reachability |
| `ops/live_billing_prepare.py` | **No** (may create Checkout Session URL only) | Pending Payment + session JSON; human must pay |
| `ops/live_billing_verify.py` | **No** | PASS/FAIL ledger, webhook, credits, amounts |

Session files: `ops/live_billing_sessions/` (gitignored).

---

## What remains unverified after a single-provider USD pass

- Other processors not exercised in the same run  
- Non-USD currencies / local payment methods  
- Partial refunds, disputes/chargebacks, subscription renewals  
- Production webhook latency under provider IP ranges at scale  

Update this doc’s result tables and flip Status to **PASS** or **FAIL** only from verifier JSON — never from manual “looks fine.”
