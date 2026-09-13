# Launch gate evidence — AcademicCheck AI

Date: 2026-09-07  
Commit basis: `cursor/production-hardening`  
Rule: a gate passes only with measurable evidence. Unrun drills fail.

## P0 — release blocked

| Item | Root cause | Components | Business impact | Deploy impact | Remediation | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| Live billing uncertified | No provider keys or live events in this environment | billing, Stripe, Paystack, Flutterwave | Double charge / missed grant | Do not take paid traffic | Run $1/₵1/₦100 success, fail, refund, replay on each provider | Signed dashboard receipts + webhook logs |
| Restore unexecuted | Managed Postgres not attached here | database, Alembic | Irreversible draft/payment loss | Do not store real tenants | Backup → delete → restore; compare `ops/validate_restore.py` counts | **Local Docker restore matched 100k assignments / 1M findings. Managed PITR still required.** |
| Workers unproven | Redis/RQ not running in CI | queue, analysis | Lost or duplicate analysis | Do not set REQUIRE_QUEUE until workers exist | 1/5/10 workers, 1000 jobs | **Local 1000 jobs 0 lost. Staging + 5k–50k still required.** |
| Secrets not in a manager | Env files are not a secret manager | config, host | Key leak | Do not deploy with `.env` on disk | Inject JWT, FIELD_ENCRYPTION_KEY, provider keys from a manager | Host inspect: no plaintext secrets on disk |

## P1

| Item | Root cause | Remediation | Verification |
| --- | --- | --- | --- |
| No independent pentest | Pytest ≠ host attack | Commission ASVS-aligned test | Report with no open High |
| WCAG 2.2 AA unsigned | AT + deployed Lighthouse missing | Record NVDA/VO/JAWS; LHCI_URL on production | Signed AT + Lighthouse ≥ 0.98 on deployed host |
| Coverage 76% | Many adapters untested | Add tests until 90% | `pytest --cov-fail-under=90` green |
| Human AI gold missing | Labels are expert-constructed | Lecturer review sample | Signed gold revision |

## P2

Load tests at 100/1000/10000 users; blue-green rollback rehearsal; pip-audit enforced.

## P3

Admin MFA; enforced dependency CVEs.

---

## Category scorecard

| Category | Current | Target | Actions completed (this pass) | Evidence | Remaining risks | Pass |
| --- | ---: | ---: | --- | --- | --- | --- |
| Tenant isolation | 100 | 100 | Version-document IDOR closed; matrix includes lists, versions, admin, anonymous | `tests/test_isolation.py` | Live-host retest still required | **Pass (repo)** |
| Security | 92 | 98 | Argon2id, family refresh revoke persisted, AES-256-GCM v2, upload JS/macro guards, prompt layering | `tests/test_security_hardening.py`, `tests/test_security_cert.py`, `docs/SECURITY_REPORT.md` | No pentest; no secret manager; no MFA | **Fail** |
| Billing | 88 | 99 | Ledger: refund, partial, replay, out-of-order, upgrade, expiry | `tests/test_billing_critical.py` | Live providers uncertified | **Fail** |
| AI quality | 87 | 98 | CIs + circularity flags; held-out n=120 labeled; red-team 0/1210; verification never-invent | `eval_report.json`, `test_ai_eval_harness.py` | n=17–35 per analyzer; CI lows 0.82–0.90; lecturer n=0; live LLM n=0 | **Fail** |
| Testing | 79 | 95 | 166 tests this pass; coverage **79%** measured; CI fail-under 70 | pytest `--cov` TOTAL 79% | Below 90% | **Fail** |
| Reliability | 92 | 98 | Stuck-job reaper; local restore; RQ 1000; PG/Redis chaos | `cert_restore_results.json`, `cert_queue_results.json`, `cert_chaos_results.json` | Managed PITR, 99.95% uptime, live providers | **Fail** |
| Production readiness | 82 | 98 | Local restore + workers + connect_timeout | same + `docs/PRODUCTION_READINESS.md` | Secret manager, image scan, staging HA | **Fail** |
| Accessibility | 93 | 98 | Live Playwright axe on public + authenticated app/admin/report; PDF extract/title; local LH 100 on 5 public routes | `npx playwright test` auth+public; `test_pdf_a11y.py`; `docs/A11Y_LIGHTHOUSE.md` | NVDA/VO/JAWS unrun; Lighthouse not on a deployed URL; PDF not PAC | **Fail** |
| Scalability | 69 | 98 | PG 1M EXPLAIN; RQ 1000; k6 100 VU | `ops/cert_postgres_results.json`, `cert_queue_results.json`, `cert_k6_summary.json` | p95 SLO fail; 1k–50k VUs; 5M/10M; R2; LB | **Fail** |

**Overall: 87 / 100. Launch: NO-GO.**

Gates passed: 1 of 9 (tenant isolation in the repository suite).

create_all remains in development/test and in Alembic `001` only. Production and staging do not call it at startup. Forward migrations are `002` through `006`.
