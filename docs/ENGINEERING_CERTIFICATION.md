# Final Engineering Certification Report — AcademicCheck AI

Date: 2026-09-07  
Verdict: **NO-GO. NOT READY FOR PRODUCTION.**  
Overall score: **87 / 100**. Launch gate 95.

This pass did not add product features. It removed silent failures, capped public lists, centralized report ownership queries, and locked those behaviors with pytest. Scores below are **unchanged** unless a new measurement exists.

## Scorecard (unchanged gates)

| Domain | Score | Gate | Pass |
| --- | ---: | ---: | --- |
| Tenant isolation (repo pytest) | 100 | 100 | Yes |
| Security | 92 | 98 | No |
| Accessibility | 93 | 98 | No |
| Billing | 88 | 99 | No |
| AI quality | 87 | 98 | No |
| Reliability | 93 | 98 | No |
| Operations | 58 | 98 | No |
| Disaster recovery | 74 | 98 | No |
| Production readiness | 82 | 98 | No |
| Scalability | 69 | 98 | No |
| Observability | 70 | 98 | No |
| Testing / coverage | 79 | 90 | No |
| Uptime readiness | 18 | 98 | No |

Isolation 100 applies to **implemented HTTP surfaces in this repository’s test suite** only.

## Pack index

1. `docs/ENGINEERING_TECHNICAL_DEBT.md`
2. `docs/ENGINEERING_ARCHITECTURE_REVIEW.md`
3. `docs/ENGINEERING_DATABASE_REPORT.md`
4. `docs/ENGINEERING_API_REPORT.md`
5. `docs/ENGINEERING_TESTING_REPORT.md`
6. `docs/ENGINEERING_PERFORMANCE_REPORT.md`
7. `docs/ENGINEERING_RELIABILITY_REPORT.md` (+ `ENGINEERING_ERROR_HANDLING.md`)
8. `docs/ENGINEERING_SECURITY_REPORT.md`
9. `docs/ENGINEERING_OBSERVABILITY_REPORT.md`
10. `docs/ENGINEERING_DEPLOYMENT_REPORT.md`
11. `docs/ENGINEERING_MAINTAINABILITY_REPORT.md` (+ standards / playbooks)
12. This file

## Issues (required fields)

### EQ-01 Report PDF used `db.get` without eager scores

- **Location:** `backend/app/api/v1/reports.py` `download_pdf`
- **Root cause:** Extra query + lazy `scores` on PDF build
- **Impact:** Extra round-trips; ownership expressed in Python after load
- **Fix:** `_owned_report` + `selectinload(AnalysisReport.scores)` + `user_id` in WHERE
- **Verification:** `test_pdf_download_eager_loads_scores`; isolation 404
- **Evidence:** pytest this pass
- **Remaining risk:** PDF still CPU-bound on the API thread (EQ-12)

### EQ-02 Share/revoke duplicated ownership `db.get`

- **Location:** `create_share`, `revoke_share`
- **Root cause:** Copy-paste fetch then `report.user_id != user.id`
- **Impact:** Inconsistent IDOR pattern vs GET report
- **Fix:** `_owned_report`
- **Verification:** source + `test_isolation.py`
- **Evidence:** pytest this pass
- **Remaining risk:** None beyond general IDOR live-host pentest

### EQ-03 Public share lazy-loaded scores

- **Location:** `_shared_report`
- **Root cause:** Serialize reads `report.scores` without `selectinload`
- **Impact:** Extra query per share view
- **Fix:** `selectinload(AnalysisReport.scores)`
- **Verification:** `test_pdf_download_eager_loads_scores` reads `_shared_report`
- **Evidence:** pytest this pass
- **Remaining risk:** Share still returns up to 80 findings without a page query

### EQ-04 Unbounded public blog/FAQ

- **Location:** `backend/app/api/v1/public.py`
- **Root cause:** No SQL LIMIT
- **Impact:** Large JSON if content tables grow
- **Fix:** `.limit(50)` / `.limit(100)`; JSON shape `{items}` unchanged
- **Verification:** `test_public_lists_are_capped`
- **Evidence:** pytest this pass
- **Remaining risk:** No cursor; items beyond cap are omitted (acceptable for CMS lists)

### EQ-05 Account delete swallowed storage errors

- **Location:** `backend/app/api/v1/auth.py` `delete_account`
- **Root cause:** Bare `except` without log
- **Impact:** Orphan objects invisible to ops
- **Fix:** `log.error("account_delete_storage_failed")`
- **Verification:** source review; account still returns `{ok: true}`
- **Evidence:** code
- **Remaining risk:** Delete still succeeds if blob delete fails (legal/soft-delete design)

### EQ-06 Queue helpers silent on Redis/DB errors

- **Location:** `backend/app/workers/queue.py`
- **Root cause:** `except Exception` returning 0 / -1 / False
- **Impact:** Ready/metrics look empty without a log
- **Fix:** warning events `worker_count_unavailable`, `queue_depth_unavailable`, `terminal_job_lookup_failed`
- **Verification:** `test_queue_helpers_log_unavailable_backends`
- **Evidence:** pytest this pass
- **Remaining risk:** `_job_already_terminal` still returns False on error (possible extra enqueue attempt)

### EQ-07 Duplicate CI Playwright `env` block

- **Location:** `.github/workflows/ci.yml`
- **Root cause:** Two `env:` keys on one step
- **Impact:** Last block wins; first ignored
- **Fix:** Single `env` with `A11Y_PYTHON`
- **Verification:** YAML parse / file review
- **Evidence:** workflow file
- **Remaining risk:** a11y still needs Chromium in GHA (already installed in that step)

### EQ-08 OpenAPI untyped for most routes

- **Location:** routers except auth `TokenResponse`
- **Root cause:** Handlers return `dict`
- **Impact:** Generated OpenAPI missing schemas
- **Fix:** Not applied (would change published schema); core **paths** locked
- **Verification:** `test_openapi_lists_core_contract_paths`
- **Evidence:** pytest this pass
- **Remaining risk:** Client codegen incomplete

### EQ-09 Coverage below 90%

- **Location:** `backend/app` (notably `rq_worker.py`, billing adapters, storage)
- **Root cause:** Adapters and worker entry lack pytest
- **Impact:** Regressions outside isolation/billing
- **Fix:** Not raising CI floor
- **Verification:** `pytest --cov=app` TOTAL **79%** (176 passed, 5657 stmts, 1176 missed)
- **Evidence:** `docs/TEST_COVERAGE_REPORT.md`
- **Remaining risk:** Worker SIGTERM untested in CI

### EQ-10 Worker kill leaves a stuck job

- **Location:** RQ analysis queue
- **Root cause:** SIGKILL does not run `request_stop`; one job remained `queued`
- **Impact:** User analysis hangs until reaper (900s) or manual intervene
- **Fix:** Not claimed this pass
- **Verification:** `ops/cert_worker_death.json`
- **Evidence:** 11/12 completed, stuck=1, 2026-09-07T10:52:58Z
- **Remaining risk:** Production worker crash

### EQ-11 HTTP p95 fails at 100 in-flight

- **Location:** `/api/live` on 4 uvicorn workers
- **Root cause:** Event-loop / process saturation (not app SQL)
- **Impact:** SLO 500 ms missed
- **Fix:** None this pass (no infra scale)
- **Verification:** `ops/cert_http_results.json` live_100 p95 1129.311 ms
- **Evidence:** 2026-09-07T12:16:16Z
- **Remaining risk:** Worse under `/api/ready` (p95 2394 ms at 50 in-flight)

### EQ-12 Sync PDF on API thread

- **Location:** `download_pdf` → `build_pdf_report`
- **Root cause:** Report PDF is request-path CPU
- **Impact:** Head-of-line blocking
- **Fix:** Not moved to RQ (UX/API change)
- **Verification:** code inspection
- **Evidence:** `reports.py`
- **Remaining risk:** Concurrent PDF downloads

### EQ-13 `engine.py` size / SRP

- **Location:** `backend/app/services/analysis/engine.py`
- **Root cause:** All heuristic analyzers in one module
- **Impact:** Review cost
- **Fix:** Not split (F1 CI coupling)
- **Verification:** AI quality tests still the gate for behavior
- **Evidence:** architecture review
- **Remaining risk:** Accidental F1 drop on refactor

### EQ-14 Service layer raises HTTPException

- **Location:** `services/auth.py`, `billing.py`, `credits.py`, `entitlements.py`
- **Root cause:** FastAPI types in domain
- **Impact:** Hidden coupling
- **Fix:** Not inverted this pass
- **Verification:** grep HTTPException in services
- **Evidence:** architecture review
- **Remaining risk:** Harder non-HTTP reuse

### EQ-15 OFFSET pagination

- **Location:** assignment list, findings page
- **Root cause:** JSON `page`/`total` contract
- **Impact:** Deep pages
- **Fix:** Not changed (API shape freeze)
- **Verification:** EXPLAIN at 100k used indexes (prior)
- **Evidence:** `docs/ENGINEERING_DATABASE_REPORT.md`
- **Remaining risk:** Deep OFFSET at 5M+ (unloaded)

### EQ-16 Process-local metrics / no Grafana

- **Location:** `app/core/metrics.py`
- **Root cause:** In-memory counters
- **Impact:** Lost on restart; no hosted dashboards
- **Fix:** Prometheus exposition exists; Grafana **not deployed**
- **Verification:** metrics pytest; no Grafana artifact
- **Evidence:** `docs/ENGINEERING_OBSERVABILITY_REPORT.md`
- **Remaining risk:** Blind ops in production

### EQ-17 Live billing uncertified

- **Location:** Stripe/Paystack/Flutterwave
- **Root cause:** No provider keys
- **Impact:** Cannot take paid traffic
- **Fix:** Infra/keys — not mocked
- **Verification:** `ops/cert_payment_keys.json`
- **Evidence:** all `*_present: false`
- **Remaining risk:** Double grant if keys added without live drill

### EQ-18 Managed PITR missing

- **Location:** database hosting
- **Root cause:** Docker-local dump only
- **Impact:** RPO = last `pg_dump`
- **Fix:** Not mocked
- **Verification:** `ops/cert_restore_audit.json` `managed_postgres: false`
- **Evidence:** RTO 21.317 s local only
- **Remaining risk:** Production data loss

### EQ-19 No independent pentest / secret manager / MFA

- **Location:** host, IAM, admin UI
- **Root cause:** Out of repo pytest
- **Impact:** Unknown host Highs; secrets on disk
- **Fix:** Not added as product MFA
- **Verification:** absent reports
- **Evidence:** `docs/SECURITY_REPORT.md`
- **Remaining risk:** Launch legal/security

### EQ-20 5M/10M and 1k–50k users unrun

- **Location:** DB load / k6
- **Root cause:** Drills not executed
- **Impact:** Scalability unknown
- **Fix:** None
- **Verification:** `not_run` arrays in cert JSON
- **Evidence:** `cert_http_results.json`, `cert_postgres` docs
- **Remaining risk:** Capacity planning invalid beyond measured 100k/1M and 100 VU

## This-pass verification summary

| Check | Result |
| --- | --- |
| `tests/test_engineering_quality.py` | Pass |
| `tests/test_scale_hardening.py` | Pass |
| `tests/test_isolation.py` | Pass (re-run with quality job) |
| Full `--cov` TOTAL | **79%** (176 passed, 5657/1176) |
| New k6 / chaos / restore | **Not re-run**; prior artifacts cited |
| Production launch | **FAIL** |

## Remaining risk (roll-up)

Paid traffic, managed database, secret manager, pentest, 90% coverage, p95 SLO at 100+ in-flight, worker-kill stuck job, Grafana/OTel, 99.95% uptime.

**Certification: not granted.**
