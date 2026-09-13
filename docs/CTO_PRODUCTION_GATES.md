# CTO production gates — AcademicCheck AI

Date: 2026-09-09 (Security/Billing continuation)  
Evidence: `docs/SECURITY_AUDIT.md`, `docs/OBSERVABILITY_READINESS.md`, `docs/ACCESSIBILITY_AUDIT.md`, `docs/OPERATIONS_READINESS.md`, `ops/cert_observability_validate.json`, `ops/cert_alerting_proof.json`, `tests/test_security_mfa_jwt.py`, `tests/test_billing_reconcile_alert.py`.

## Gate table (old → new)

Every category with open Excluded/Bucket B items is **explicitly capped below 95**. None clear a 95+ gate.

| Category | Old | New | Δ | Gate | Pass | Cap note | Evidence |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| Security | 93 | **94** | +1 | 98 | No | Cap: no pentest/secret manager; MFA **code-complete**, staging drill pending (HAL-07–09) | Session limit; breach denylist; lab attacks; `docs/SECURITY_READINESS.md` |
| Billing | 94 | **94** | 0 | 99 | No | Cap: live PSP **AWAITING HUMAN** (HAL-01–04). FSM + webhook freshness + grant drift fail-closed are pytest-proven — still not live-certified. | `docs/FINANCIAL_INTEGRITY_CERTIFICATION.md`; `test_billing_integrity_fsm.py`; sandbox 56 passed |
| Reliability | 94 | **94** | 0 | 98 | No | Cap: worker-kill stuck + provider kill (HAL-14–15). Timeouts/circuits/RQ jitter pytest-proven; kill 12/12 still FAIL. | `test_reliability_hardening.py` 19-pack; `docs/RELIABILITY_CERTIFICATION.md` |
| Scalability | 69 | **72** | +3 | 98 | No | Cap: prod-scale load unrun (HAL-13) | Migration 008; compose pool; load_test.js profiles asserted **not executed at scale** |
| Disaster recovery | 78 | **82** | +4 | 98 | No | Cap: managed PITR/WAL; **prod dump/restore AWAITING HUMAN**; multi-region unrun | Restore re-run 20:22Z RTO 27.446s + FK orphans 0; `docs/DISASTER_RECOVERY_READINESS.md` |
| Observability | 80 | **88** | +8 | 98 | No | Cap: hosted Grafana/PagerDuty (HAL-10–11). Code-complete metrics/OTEL/dashboards/PD payload; local stack validate. | `docs/OBSERVABILITY_READINESS.md`; `test_observability_metrics.py`; `test_logging_hygiene.py`; `ops/validate_observability_stack.py` |
| Accessibility | 94 | **94** | 0 | 98 | No | Cap: human AT sign-off (HAL-18). Automated+keyboard coverage expanded (axe CI + keyboard.spec + pa11y script). | `docs/ACCESSIBILITY_AUDIT.md`; `frontend/a11y/keyboard.spec.ts` |
| Testing | 79 | **81** | +2 | 90 | No | Cap: ≥90% not reached (HAL-21) | **80.98%** TOTAL; 208 passed (`ops/cert_pass3_coverage.txt`) |
| Operations | 62 | **78** | +16 | 98 | No | Cap: on-call unassigned (HAL-11). Tooling/runbooks/deploy/status complete. | `docs/OPERATIONS_READINESS.md`; `ops/deploy_compose.sh`; `ops/rollback_compose.sh`; `ops/status/index.html`; `docker-compose.staging.yml` |
| Deployment readiness | 84 | **88** | +4 | 98 | No | Cap: hosted staging cutover unproven; topology now mirrored in-repo | `docker-compose.staging.yml` (`REQUIRE_QUEUE=true`); ready-gated deploy |
| Production readiness | 84 | **86** | +2 | 98 | No | Cap: composite Bucket B | Aggregate of above |
| AI quality | 87 | 87 | 0 | 98 | No | Cap: lecturer gold / live LLM (HAL-16–17) | Unchanged |
| Tenant isolation (repo) | 100 | 100 | 0 | 100 | Yes* | *pytest only | Unchanged |

**Overall: 90**. Gate **95**. Still **NO-GO** (hosted observability, on-call, AT sign-off, live PSP, PITR, prod DR human drill remain). DR local/cert improved to **82**; production DR still uncapped below 95.

## Closed this pass / still open (per category)

### Security
- **Closed:** CSRF/webhook metrics; cancel IDOR; privileged TOTP MFA; JWT alg allow-list; **concurrent refresh session limit**; **expanded breach denylist**; lab attack suite; secrets allow-list for backup key.
- **Still open:** Pentest, secret manager, MFA staging/UI (HAL-09), ClamAV mandatory, blocking supply-chain in main `ci.yml`, TLS terminator proof.

### Billing
- **Closed (sandbox logic):** All 8 scenarios × 3 processors; idempotency, duplicate/OOO/concurrent webhooks, declines, refunds, signatures, reconcile.
- **Closed (this pass):** Subscription FSM (`subscription_fsm.py`); Paystack/Flutterwave freshness when timestamp present; `grant_credits` fail-closed on ledger drift; renew uses FSM `past_due`→`active`.
- **Closed (harness/ops):** Live spot-check scripts that **do not move money**; reconcile CLI + mismatch alert.
- **Still open:** Human $1 success, decline, Dashboard refund (HAL-01–03); provider cancel on delete (HAL-04). **sandbox verified; live spot-check pending**.

### Reliability
- **Closed:** DLQ + `jobs.dead_letter`; RQ SIGTERM `request_stop`; `jobs.started`/`jobs.completed`; **RQ retry jitter**; timeout inventory; circuit half-open test.
- **Still open:** Worker-kill 12/12 recover (HAL-15); live Redis/PG multi-AZ; billing/AI provider kill (HAL-14).

### Scalability
- **Closed:** `ix_payments_user_created` + security_events created_at (008); compose `DB_POOL_*`; k6 profile declaration test (no fabricated results).
- **Still open:** 1k–10k VU against provisioned staging.

### Disaster recovery
- **Closed (local/cert):** Production DR drill **package**; local restore audit **re-executed 2026-09-09** (delete/DROP/migration/destroy); local object checksum restore; Redis AOF restart; encrypted dump crypto; Phase 13 automation scripts.
- **Still open / human:** Operator must run `docs/PROD_DR_DRILL.md` Steps B–E against real prod; managed PITR; WAL replay; S3/CRR; multi-region; combined drill (HAL-05–06, HAL-05b). **Score does not claim production restore until `ops/cert_prod_dr_verify.json` shows PASS.**

### Observability
- **Closed (engineering):** Structured logging hygiene CI; per-endpoint metrics + gauges; OTEL tracing module; Grafana JSON + Prometheus rules validated by `ops/validate_observability_stack.py`; local observability compose; PagerDuty Events API v2 payload in `alerting.py`; Slack/file alerting already proven.
- **Still open:** Hosted Prometheus/Grafana/Alertmanager scrape (HAL-10); hosted PagerDuty + on-call (HAL-11). **Ready to activate, pending hosting.**

### Accessibility
- **Closed (automation):** axe CI + Playwright routes; keyboard.spec (login/settings trap/billing); pa11y script; ARIA live/alert patterns; `docs/ACCESSIBILITY_AUDIT.md`.
- **Still open:** Human screen-reader sign-off (HAL-18).

### Testing
- **Closed:** Remeasured TOTAL **81%**; Pass3 suite; 208 tests green.
- **Still open:** ≥90% floor; full E2E DOCX/mobile.

### Operations / Deployment / Production readiness
- **Closed:** Complete runbooks (incl. DB pool + rollback); `ops/deploy_compose.sh` + `ops/rollback_compose.sh`; ready-gated cutover; `docker-compose.staging.yml`; status page `ops/status/index.html`; `docs/OPERATIONS_READINESS.md`.
- **Still open:** Named on-call roster (HAL-11); hosted staging drill evidence.

### AI quality
- **Closed:** Nothing this pass (Bucket B).
- **Still open:** Lecturer labels; live provider eval.

## Requirements matrix counts

FAIL remains **3** (REQ-72, REQ-92, REQ-107). PASS/PARTIAL recount not re-litigated for product FAILs.

## Human Action List

Confirmed accurate; no removals. See `docs/HUMAN_ACTION_LIST.md` (Pass 3 note: A-PAY now has a **code** metric but HAL-10 still required for hosted scrape).

## Launch

**APPROVED FOR LAUNCH: NO** — overall **90 < 95**; hosted observability, on-call, AT sign-off, live PSP, managed PITR, coverage≥90, and human QC remain by design.
