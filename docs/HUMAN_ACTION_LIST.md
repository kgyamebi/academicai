# Human Action List — Bucket B (Pass 2 + Pass 3 confirm)

Date: 2026-09-07 (Pass 3)  
Rule: these items **cannot** move to PASS from inside this agent environment.

Pass 3 confirmation: **all HAL-01–HAL-25 remain open**. No HAL was closed. Notes only:

| ID | Pass 3 note |
| --- | --- |
| HAL-01–04 | Webhook **mock** coverage expanded; live charges still required |
| HAL-10 | A-PAY now has `billing.failed_payments` in alert-rules.yml — still **not scraped** by a hosted Prometheus |
| HAL-21 | Coverage measured **80.98%** — still below 90 |

| ID | Requirement / gate gap | What a human must do | Evidence required to flip PASS |
| --- | --- | --- | --- |
| HAL-01 | Live Stripe certification (REQ-51/53, Billing gate) | Run `docs/LIVE_TRANSACTION_VERIFICATION.md` with `LIVE_BILLING_PROVIDER=stripe` and live keys: human pays $1 success, decline, Dashboard refund; verifier PASS | `ops/cert_live_billing_verify_*.json` + updated `LIVE_TRANSACTION_VERIFICATION.md` |
| HAL-02 | Live Paystack certification | Same drill with Paystack secret + webhook secret; NGN/GHS as applicable | Event IDs + signed webhook logs |
| HAL-03 | Live Flutterwave certification | Same drill with FLW secret + verif-hash | Event IDs + signed webhook logs |
| HAL-04 | Provider cancel on account delete (REQ-98) | Call Stripe/Paystack/FLW subscription cancel APIs from delete path **after** keys exist; verify in provider dashboards | Provider API response IDs in audit log |
| HAL-05 | Managed Postgres PITR (DR gate) | Provision managed Postgres with PITR; execute restore-to-timestamp drill | Vendor restore ticket + row fingerprint match |
| HAL-06 | WAL replay drill | Run restore from archived WAL on a disposable instance | Restore log + `ops/cert_restore_*` update |
| HAL-05b | Production logical dump/restore drill | Run `docs/PROD_DR_DRILL.md` Steps B–E with real prod read-only credentials into isolated Docker; paste timing + `ops/cert_prod_dr_verify.json` | Verify verdict PASS + RTO/RPO filled |
| HAL-07 | Independent pentest (Security gate) | Contract third-party pentest of staging host | Pentest report PDF; Critical/High = 0 |
| HAL-08 | Secret manager | Wire AWS Secrets Manager / GCP Secret Manager / Vault; remove disk `.env` for prod | Config showing secrets loaded from manager only |
| HAL-09 | MFA staging drill | Backend TOTP enroll/challenge/admin gate is **code-complete** (`test_security_mfa_jwt.py`). Human: enroll seed admin on staging + prove login | Staging login screenshots + auth tests green |
| HAL-10 | Hosted Prometheus + Grafana + Alertmanager | Deploy scrapers against `/api/metrics/prometheus`; import `ops/grafana/*.json`; load `ops/prometheus/alert-rules.yml` | Screenshot of live panels + firing test alert |
| HAL-11 | PagerDuty / on-call | Assign named primary/secondary; route Alertmanager; run page drill | Ack timestamp in PD + `ONCALL` roster |
| HAL-12 | ClamAV mandatory in prod | Deploy ClamAV sidecar; fail upload if scanner down | Config + malware sample reject log |
| HAL-13 | Production-scale load | k6/locust against staging at 1k–10k VU authenticated routes | `ops/cert_k6_*` for those profiles green |
| HAL-14 | billing_provider_kill chaos | Kill Stripe/Paystack/FLW network path in staging; observe circuit + no fake paid state | Update `ops/cert_chaos_results.json` |
| HAL-15 | Worker-kill stuck job (Reliability) | Reproduce and fix until 12/12 recover; re-run `ops/cert_worker_death.json` | `pass: true` artifact |
| HAL-16 | Lecturer / human QC gold (REQ-92, AI gate) | Staff reviewers; fill `reviewer_labels.jsonl`; run agreement metrics | n≥ agreed sample + kappa report |
| HAL-17 | Live LLM eval | Run held-out against paid OpenAI/Anthropic/Gemini with keys | `ops/cert_ai_results.json` `live_provider: true` |
| HAL-18 | NVDA / VoiceOver / JAWS (A11y gate) | Manual AT pass on check → report → share | Signed a11y checklist |
| HAL-19 | TLS terminator proof | Capture TLS1.2+ config on real LB/CDN | SSL Labs or equivalent export |
| HAL-20 | Uptime SLO window | Measure ≥30 days (or agreed window) ready/5xx | `ops/cert_uptime_*` multi-day |
| HAL-21 | Coverage ≥90% (Testing gate) | Run full `pytest --cov` in CI; raise floor only when green | Coverage HTML + CI log ≥90% (currently **80.98%**) |
| HAL-22 | REQ-72 Notifications product | Product decision to ship in-app notifications API+UI+worker | Specs + tests + UI |
| HAL-23 | REQ-107 Ecosystem | Shared auth/billing with sibling products — business architecture | Shared package or SSO contract |
| HAL-24 | Blocking supply-chain CI | Make `pip-audit` / `npm audit` blocking in main `ci.yml` after fixing vulns | Green CI without `\|\| true` |
| HAL-25 | Staging REQUIRE_QUEUE | Deploy staging with Redis+workers; no inline fallback | Staging ready checks + job IDs |

## Newly discovered (Pass 3)

| ID | Gap | Action |
| --- | --- | --- |
| HAL-26 | Flutterwave/Paystack webhook previously passed string UUIDs to `db.get` (fixed in Pass 3) | After deploy, re-test live FLW/Paystack reference lookups on staging (ties to HAL-02/03) |

Writing another runbook does **not** close these items.
