# Launch Audit Certification — AcademicCheck AI

Date: 2026-09-07  
Auditor role: independent QA / security / SRE / product / academic integrity / SaaS launch / DevSecOps.  
Spec: original AcademicCheck AI requirements 1–108.

## Verdict

# DO NOT LAUNCH

Launch rule failed: failed requirements remain; critical and high risks remain; production deployment unproven; live billing unproven; managed data-loss controls unproven.

**APPROVED FOR LAUNCH** is not issued.

Scores are **not** increased. Overall remains **87 / 100**. Isolation 100 is repository pytest only.

## PASS requirements (selected; full list in RTM)

REQ-2, 5.1, 5.2, 5.3, 6, 7, 9, 11, 16, 17, 20, 24, 25, 29, 32, 34, 36, 39, 40, 41, 42, 45, 46, 48, 49, 50, 54, 57, 58, 60, 62, 70, 75, 76, 77, 78, 80 (repo), 81, 88, 90, 93, 94, 95, 101, 105.

## PARTIAL requirements

REQ-1, 3, 4, 8, 10, 12–15, 18, 19, 21–23, 26–28, 30, 31, 33, 35, 37, 38, 43, 44, 47, 51–53, 55, 56, 59, 61, 63–69, 71, 73, 74, 79, 82 (overall), 83–87, 89, 91, 96–100, 102–104, 106, 108, plus REQ-64.5–64.20 sitemap gaps.

## FAILED requirements (code-absent)

| ID | Blocker |
| --- | --- |
| REQ-72 | In-app notifications unused |
| REQ-92 | Human review QC empty |
| REQ-107 | Ecosystem integration absent |

REQ-82.1 / REQ-82.2 closed this pass (`GET /api/citations`, `POST /api/citations/verify`, isolation pytest).

## Production proofs that fail the launch rule (even if architecture is PARTIAL)

- Live Stripe / Paystack / Flutterwave  
- Managed PostgreSQL PITR  
- Secret manager  
- Independent pentest  
- Hosted tracing/dashboards/alerting  
- HTTP p95 at 100 in-flight  
- Worker-kill zero stuck  
- Coverage 90%  
- Staging `REQUIRE_QUEUE`  
- WCAG AA AT sign-off  

## Critical risks

1. Paid traffic without live PSP certification → double-charge / missed grant.  
2. Student data without managed PITR / encrypted backups → irreversible loss.  
3. Production without secret manager and pentest → credential and IDOR unknown.

## High risks

- Provider subscription not cancelled on account delete (local status only).  
- Worker-kill stuck job.  
- AI quality claimed without lecturer gold (REQ-92 FAIL).  
- Citation verification HTTP exists (isolation pytest); live Crossref uncertified.  
- Accessibility AA unsigned.  
- Admin UI insufficient for spec ops.

## Medium risks

- Notifications FAIL.  
- Incomplete sitemap vs SEO seed.  
- OFFSET pagination at untested 5M.  
- Guest purge only when analysis reaper runs.  
- Grammar/citation styles incomplete vs full spec.

## Low risks

- REQ-107 ecosystem.  
- shadcn vs custom Tailwind.  
- RQ vs Celery (spec allows RQ).  
- Separate finding tables vs unified `analysis_findings`.

## Phase 10 remediations actually performed

Not a feature expansion:

1. Guest expired document purge + pytest.  
2. Account deletion cancels local active/past_due/trialing subscriptions + pytest.

Not performed (would be new product or mocked infra): notifications, citation REST, human review UI, live PSP, Grafana, SSO, version restore.

**No FAIL-free state was reached. Repeat-until-green is blocked on infrastructure and product-scope freeze.**

## Exact launch blockers

1. Failed spec IDs: REQ-72, REQ-82.1, REQ-82.2, REQ-92, REQ-107.  
2. Critical: live billing, managed PITR, secret manager.  
3. High security: no pentest; provider cancel gap.  
4. Data-loss: no WAL PITR; dumps plaintext.  
5. Academic integrity QC: no human gold (REQ-92).  
6. Production deploy: no CD, no image scan, no hosted observability, SLO p95 fail at 100 in-flight.

Isolation: no cross-tenant access **in pytest**. Not a host certificate.

Billing corruption: pytest ledger OK; **live paths unproven**.

Academic integrity **copy and non-generation**: PASS. Human QC: FAIL.

Production deployment requirements: **not satisfied**.
