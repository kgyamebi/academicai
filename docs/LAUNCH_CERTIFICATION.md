# Launch certification — AcademicCheck AI

Date: 2026-09-07  
Rule: a gate passes only with measurable evidence. Unrun drills are not certificates.

## 1. Exact remaining blockers (P0)

1. Live Stripe, Paystack, and Flutterwave charge / refund / webhook drills with real keys.
2. Managed PostgreSQL provisioned, Alembic at head (**006**), **executed** backup + restore with matching row counts — **local Docker restore passed; managed PITR still open.**
3. Production/staging API with `REQUIRE_QUEUE=true` and at least one live RQ worker; 1,000-job run with zero lost/duplicate jobs — **local 1000-job pass; staging still open.**
4. Secrets only in a secret manager (`FIELD_ENCRYPTION_KEY`, JWT ≥ 32 bytes, provider keys).
5. Independent penetration test against a deployed host.
6. Axe + NVDA/VoiceOver walkthrough recorded on the deployed UI.
7. Backend coverage is **79%** (measured this pass, 166 tests). CI floor is 70% overall / 75% critical packages. 90% is not met.
8. Third-party human review of AI gold (current gold is expert-constructed, CI-gated).

## 2. Root causes

| Blocker | Cause | Services | Severity | Exploitability | Business impact | Deploy risk |
| --- | --- | --- | --- | --- | --- | --- |
| Live billing uncertified | No provider keys / live events in this repo | billing, webhooks | P0 | High if keys mis-set | Double charge, missed grant | Do not take paid traffic |
| Restore unexecuted | No managed instance attached here | postgres | P0 | n/a | Irreversible data loss | Do not store real drafts |
| Workers unproven at load | Redis/RQ not running in CI | queue | P0 | Medium (lost analysis) | Failed checks, credit disputes | Do not enable REQUIRE_QUEUE until workers exist |
| No pentest | Code tests ≠ host attack | API, auth | P1 | High for missed IDOR | Tenant leak | Delay public launch |
| AA unsigned | Static checks ≠ AT | frontend | P1 | Low/medium | Legal / exclusion | Marketing claim risk |
| Coverage < 90% | Many modules still lightly tested | all | P1 | n/a | Regressions | Raise floor only when hit |
| Human gold missing | Labels are rule-based, not lecturer-reviewed | analysis | P1 | n/a | Wrong feedback trust | Do not claim “human-validated AI” |

## 3. Required code changes (done in-repo vs still open)

Done: version-document IDOR closed (`owned_document` + assignment match); isolation matrix expanded; refund/out-of-order billing; CSRF/upload/entitlement tests; a11y static gates; AI F1 CI floors.

Still open: nothing else that can be closed without infrastructure except remaining coverage gaps.

## 4. Required infrastructure changes

Managed PostgreSQL + PITR, Redis + N RQ workers, object storage, secret manager, staging and production env separation, host metrics/alerts from `docs/ALERTS_AND_SLOS.md`.

## 5. Required database changes

No new product tables. Apply Alembic `002` through `005` (job/finding/list composite indexes) on managed Postgres. Run `ops/validate_restore.py` before and after the restore drill.

## 6. Required test additions

Isolation now covers assignments, documents, analysis, reports, PDF, share, versions, dashboard lists, payments, coach, admin, anonymous, and document-id tamper. Still required: live provider tests, Playwright/axe on a running app, k6 at agreed VUs.

## 7. Required monitoring additions

`/api/live`, `/api/ready`, `/api/metrics` exist. Wire replica counters to the host. Alert rules are specified, not deployed.

## 8. Required security fixes

Version attach IDOR fixed. This pass: Argon2id, one-time reset/verify, AES-256-GCM field crypto, upload JS/macro guards, prompt layering. Remaining High: no pentest, secrets not in a manager, live webhook abuse untested, no admin MFA.

## 9. Required AI quality improvements

Deterministic F1 on expert gold: thesis/argument/evidence/rubric ≥ 0.95 (CI). ROC is not applicable: these classifiers are rule labels, not score-threshold models. Human review still required for a 95 **overall AI quality** claim.

## 10. Required billing improvements

Ledger tests cover success, fail, cancel, refund, partial refund, replay, out-of-order, upgrade, expiry. Live provider certification is still open.

## 11. Deployment certification checklist

- [x] Docker compose production file exists (API + worker + PgBouncer)
- [ ] Images built and scanned
- [ ] Secrets injected, not committed
- [ ] Stage env distinct from prod
- [ ] Blue-green or equivalent rollback rehearsed
- [ ] Backup + restore drill signed
- [ ] Workers registered on `/api/ready`

## 12. Launch certification checklist

- [ ] Isolation 100% on deployed host (repo suite is green)
- [ ] Live billing 99 evidence pack attached
- [ ] WCAG 2.2 AA axe + AT report attached
- [ ] Pentest with no open High
- [ ] AI human-gold sign-off
- [ ] Coverage ≥ 90%
- [ ] Load test evidence at agreed scale

## 13. Risk register

| Risk | Residual | Owner |
| --- | --- | --- |
| Payment double-grant in production | Medium until live drill | Billing |
| Tenant draft leak via missed IDOR | Low in repo tests; Medium until pentest | Security |
| Irreversible DB loss | Medium until managed PITR; local restore passed | SRE |
| Queue drop under load | Medium until 5k–50k and staging workers | SRE |
| Over-claiming AI accuracy | Medium | Product |

## 14. Final readiness score (evidence-based)

| Domain | Score | Gate | Pass |
| --- | ---: | ---: | --- |
| Tenant isolation (repo) | 100 | 100 | Yes — in automated tests after version IDOR fix |
| Billing | 88 | 99 | No |
| Security | 92 | 98 | No — family refresh revoke pytest this pass; pentest / secret manager / MFA / live billing missing |
| AI quality | 87 | 98 | No — held-out n=17–35; CI lows 0.82–0.90; no lecturer/LLM proof |
| Reliability | 93 | 98 | No — local restore audit + 1000 RQ + PG/Redis chaos; worker-kill 1 stuck; 99.95% missing |
| Production readiness | 82 | 98 | No — local drills only; no secret manager, image scan, staging HA |
| Accessibility | 93 | 98 | No — auth axe lab pass; NVDA/VoiceOver/JAWS and deployed Lighthouse still missing |
| Scalability | 69 | 98 | No — live_50 p95 490 ms pass; live_100 1129 ms fail; 1k–50k users unrun |
| **Overall** | **87** | **95** | **NO-GO** |

Isolation 100 applies to **implemented HTTP surfaces in this repository’s test suite**. It is not a live-host certificate.

P0 backlog: live payments, managed PITR, secret manager. Local restore + 1000 RQ jobs are done on Docker, not on staging.  
P1: pentest, recorded NVDA/VoiceOver/JAWS, Lighthouse on deployed URL, coverage 90%, human AI gold.  
P2: k6 1k–50k users with p95 < 500 ms, blue-green rehearsal.  
P3: MFA, pip-audit enforced.
