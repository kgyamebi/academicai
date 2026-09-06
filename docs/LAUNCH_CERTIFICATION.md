# Launch certification — AcademicCheck AI

Date: 2026-09-06  
Rule: a gate passes only with measurable evidence. Unrun drills are not certificates.

## 1. Exact remaining blockers (P0)

1. Live Stripe, Paystack, and Flutterwave charge / refund / webhook drills with real keys.
2. Managed PostgreSQL provisioned, Alembic at head, **executed** backup + restore with matching row counts.
3. Production/staging API with `REQUIRE_QUEUE=true` and at least one live RQ worker; 1,000-job run with zero lost/duplicate jobs.
4. Secrets only in a secret manager (`FIELD_ENCRYPTION_KEY`, JWT ≥ 32 bytes, provider keys).
5. Independent penetration test against a deployed host.
6. Axe + NVDA/VoiceOver walkthrough recorded on the deployed UI.
7. Backend coverage is **76%** (measured). CI floor is 70% overall / 75% critical packages. 90% is not met.
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

No new product tables. Apply Alembic `002` and `003` on managed Postgres. Run `ops/validate_restore.py` before and after the restore drill.

## 6. Required test additions

Isolation now covers assignments, documents, analysis, reports, PDF, share, versions, dashboard lists, payments, coach, admin, anonymous, and document-id tamper. Still required: live provider tests, Playwright/axe on a running app, k6 at agreed VUs.

## 7. Required monitoring additions

`/api/live`, `/api/ready`, `/api/metrics` exist. Wire replica counters to the host. Alert rules are specified, not deployed.

## 8. Required security fixes

Version attach IDOR fixed. Remaining High: untested live webhook abuse, unsigned share-link leakage if token is posted, no step-up MFA for admin.

## 9. Required AI quality improvements

Deterministic F1 on expert gold: thesis/argument/evidence/rubric ≥ 0.95 (CI). ROC is not applicable: these classifiers are rule labels, not score-threshold models. Human review still required for a 95 **overall AI quality** claim.

## 10. Required billing improvements

Ledger tests cover success, fail, cancel, refund, partial refund, replay, out-of-order, upgrade, expiry. Live provider certification is still open.

## 11. Deployment certification checklist

- [x] Docker compose production file exists
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
| Irreversible DB loss | High until restore drill | SRE |
| Queue drop under load | High until 1000-job proof | SRE |
| Over-claiming AI accuracy | Medium | Product |

## 14. Final readiness score (evidence-based)

| Domain | Score | Gate | Pass |
| --- | ---: | ---: | --- |
| Tenant isolation (repo) | 100 | 100 | Yes — in automated tests after version IDOR fix |
| Billing | 88 | 99 | No |
| Security | 88 | 95 | No |
| AI quality | 84 | 95 | No — deterministic F1 yes; human/LLM no |
| Reliability | 74 | 95 | No |
| Production readiness | 72 | 95 | No |
| Accessibility | 64 | 95 | No |
| **Overall** | **81** | **95** | **NO-GO** |

Isolation 100 applies to **implemented HTTP surfaces in this repository’s test suite**. It is not a live-host certificate.

P0 backlog: live payments, executed restore, live workers.  
P1: pentest, axe/AT, coverage 90%, human AI gold.  
P2: k6 1k–50k users, blue-green rehearsal.  
P3: MFA, pip-audit enforced.
