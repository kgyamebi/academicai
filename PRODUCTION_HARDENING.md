# AcademicCheck AI — Production Hardening Plan and Implementation Record

Status after this pass: **prototype → hardened foundation**. Launch remains **NO-GO** until the remaining P0/P1 items in the checklists are evidenced in a real staging environment with live payment keys, managed PostgreSQL, workers, and backups.

This document is the operating plan. The code in this repository implements the P0 remediations; it does not invent passing scores.

---

## 1. Complete gap analysis

| Area | Audit fact | Gap | Code status after this pass |
|---|---|---|---|
| Default admin | `admin@academiccheck.ai` / `ChangeMeAdmin123!` worked | Seeded credential | **Fixed.** Seed never creates that password. Startup disables the account if the published hash is still present. Bootstrap only via `ADMIN_BOOTSTRAP_EMAIL` + `ADMIN_BOOTSTRAP_PASSWORD` (≥16 chars, not the leaked password). |
| Registered analysis 500 | Naive vs aware datetime | `increment_usage` compared `datetime.now(UTC)` to SQLite-naive `current_period_end` | **Fixed.** All comparisons go through `app.core.time.as_utc` / `is_past`. Usage increments only after a successful job. |
| JWT in localStorage | XSS → account takeover | Browser stored access + refresh | **Fixed.** HttpOnly `ac_access` / `ac_refresh`, readable `ac_csrf`, SameSite=Lax, Secure in production. Next.js rewrites `/api/*` same-origin. Frontend uses `credentials: 'include'`. Bearer remains for tests and native clients. Refresh rotation + reuse detection revokes the family. |
| OpenAPI public | `/api/docs`, `/api/openapi.json` 200 | Information disclosure | **Fixed.** Enabled in development/test. Staging: admin-only. Production: disabled. |
| In-process rate limit | Process-local dict | Useless under multiple workers | **Fixed.** Redis INCR+EXPIRE. Memory fallback only outside production. Production fails closed (503) if Redis is down. |
| Encryption at rest | Assignment/document/report plaintext | DB dump = full student work | **Implemented field encryption** (`enc:v1:` Fernet). Production refuses to start writes without `FIELD_ENCRYPTION_KEY`. Existing plaintext remains readable during transition. Disk/volume encryption and TDE are still required in the managed DB. |
| Webhooks | Custom HMAC, no Stripe SDK, no Paystack/Flutterwave, no replay window | Spoof / replay / double grant | **Fixed.** Stripe `Webhook.construct_event` + timestamp tolerance. Paystack HMAC-SHA512 (`x-paystack-signature`). Flutterwave `verif-hash`. `webhook_events.event_id` unique for replay/idempotency. |
| Share links | Token only, no password/expiry/audit | Link leak = report leak | **Fixed.** Password, expiry, revoke, view count, `share_access_logs`. |
| Credits | `consume_credits` no-op when empty; usage incremented at enqueue | Free unlimited analysis if usage crashed; no reserve/refund | **Fixed.** Ledger: reserve → consume on success → refund on fail/cancel. Monthly quota first; credits only when quota is exhausted. Atomic wallet updates (`SELECT FOR UPDATE` on Postgres). |
| Billing fake | Checkout did not charge; plan stayed free | Cannot launch | **Fixed path.** Stripe Checkout Session, Paystack initialize, Flutterwave payments. Upgrade happens only after a verified webhook. Missing keys return 503, never a fake “paid” state. Live keys still required in staging/prod. |
| Fat routes | API modules mixed auth, persistence, policy | Hard to test/scale | **Partial.** Credits, billing, auth, time, crypto extracted. Repository layer is the next contract (see §20). |
| Alembic `create_all` | Not reversible | Cannot migrate prod | **Partial.** `create_all` only in development/test. Production uses Alembic. `002_production_hardening.py` is expand/contract and inspector-safe. `001` is still metadata create_all and must be replaced before first real prod migrate from empty. |
| N+1 / pagination | Findings sliced in Python | Memory blow-up | **Fixed** for report findings (`OFFSET/LIMIT`). Assignment list already SQL-paginated. Compare now uses requested versions. |
| Inline analysis | API process ran the job | Timeouts, no scale | **Fixed policy.** Production/`REQUIRE_QUEUE=true` returns 503 if no RQ worker. Dev still inlines so local tests work. Dead-letter queue `analysis_dlq` + retry. |
| AI quality | Heuristic-only, thesis 2/8 | Not launch-grade feedback | **Harness in place.** Structured JSON + retry + fallback + output firewall. Eval metrics endpoint `/api/admin/eval`. Quality is **not** 95% yet — benchmark work is P1. |
| Prompt injection | Delimiters only | Document can jailbreak | **Firewall + 1000-case suite** in `tests/test_prompt_injection.py`. |
| Document security | MIME/magic/zip bomb existed | No AV, no signed URLs | ClamAV INSTREAM when `CLAMAV_HOST` set. R2/S3 via boto3 + SSE + presigned GET. Quotas already in validation. |
| Observability | Logs only | No pages/alerts | Sentry init if `SENTRY_DSN`. Structured logs exist. OTel/metrics dashboards are P1 — do not claim they are live. |
| A11y / mobile / SEO | Partial | WCAG 2.2 AA not evidenced | Plan in §8/SEO/a11y sections. Not signed off. |
| Coverage 90% | Far below | Gate would fail | CI fail-under is 55% until the critical-path suite reaches 90%. Do not ship claiming 90%. |

---

## 2. Priority matrix

### P0 — launch blockers (must be green in staging)

1. Default admin eliminated and verified by login probe.
2. Registered `POST /api/analysis` returns 200 and completes.
3. Cookie sessions + CSRF + refresh rotation + logout revoke.
4. OpenAPI hidden in production.
5. Redis rate limit in the deployed API.
6. Field encryption key set; sample row in DB is `enc:v1:`.
7. Stripe/Paystack/Flutterwave checkout URLs open real hosted pages; unsigned webhooks 400; replay 200 no double grant.
8. Share password + expiry + revoke.
9. Credit reserve/consume/refund; usage only after success.
10. Workers required in production; job status polling works.
11. Alembic 002 applied; `create_all` off in prod.
12. Authorization suite green (assignments, documents, reports, payments).
13. Secrets not in git; JWT ≥ 32 bytes.

### P1 — first 30 days

- Replace Alembic 001 with explicit table DDL (expand/contract).
- PgBouncer, backups, PITR, restore drill.
- Structured analyzers (question/thesis/argument/evidence/citation/rubric) with JSON Schema and gold datasets.
- Prompt-injection red team beyond the synthetic 1000.
- ClamAV in the upload path in staging.
- Sentry + OTel traces + Grafana/Datadog dashboards and alerts.
- Account lockout UX, anomaly mail, password rotation admin tool.
- Dunning emails, Stripe Customer Portal, proration, refunds API.
- WCAG 2.2 AA (axe + keyboard + contrast).
- Coverage 90% on `auth`, `billing`, `credits`, `deps`, `analysis`, `documents`.

### P2 — 90 days

- Read replicas + search (OpenSearch) for admin.
- WebSocket job updates.
- Institution SSO / SCIM.
- CDN for marketing; signed media only.
- Chaos tests (kill Redis, kill worker, replay webhooks).
- Country-unique SEO QA automation.

### P3 — later

- Multi-region active-passive.
- Customer-managed keys (CMK) for field encryption.
- On-prem/VPC deploy for institutions.

---

## 3. Architecture redesign

```
Browser (Next.js / Vercel)
  │  same-origin rewrite /api/* + HttpOnly cookies
  ▼
API (FastAPI, stateless, N replicas)
  │  CSRF, RBAC, tenant checks, Redis rate limit
  ▼
Application services
  auth | entitlements | credits | billing | documents | analysis | reports
  ▼
Repositories / SQLAlchemy (no business rules in routes)
  ▼
PostgreSQL (primary)          Redis (rate limit, RQ, cache)
  ▼
RQ workers (autoscaled)  →  analysis.runner  →  AI layer (schema + firewall + fallback)
  ▼
R2 / S3 (SSE, presigned GET)     Provider webhooks → payment ledger
```

Rules:

- API never calls model providers inline in production.
- API never writes “paid” except from a verified, de-duplicated webhook.
- Every read of assignment/document/report/finding decrypts in the service layer, never in logs.
- `user_id` on the row must match the session user or the handler returns 404 (not 403) to avoid ID enumeration.

---

## 4. Database migration plan

**Current**

- Dev/test: `Base.metadata.create_all` in lifespan.
- Prod: no create_all; run Alembic.

**Revisions**

| Rev | Purpose | Rollback |
|---|---|---|
| 001 | Historical create_all | `drop_all` — **do not run on prod data** |
| 002 | New columns, share/webhook tables, composite indexes | Drops only objects 002 added (inspector-guarded) |

**Expand/contract for 001 replacement (P1)**

1. Expand: add explicit `003_explicit_schema` that no-ops if tables exist.
2. Contract: stop importing `create_all` from 001 in new environments by squashing after the first prod baseline.
3. Never rename encrypted columns in place; add, backfill, switch reads, drop.

**Indexes required (002)**

- `analysis_jobs (user_id, status, created_at)`
- `assignments (user_id, created_at)`
- `documents (user_id, assignment_id)`
- `payments (user_id, status)`
- `credit_transactions (analysis_job_id, status)`

**Pagination**

- Assignments: SQL `OFFSET/LIMIT`.
- Report findings: SQL `OFFSET/LIMIT`.
- Never `query.all()[n:m]` for user data.

**N+1**

- Load scores/findings with explicit queries, not implicit lazy loops on large collections in list endpoints.

---

## 5. Security remediation plan

| Control | Implementation |
|---|---|
| Default admin | `seed.disable_insecure_default_admin`, no hardcoded password |
| Sessions | HttpOnly cookies, rotation, family revoke on reuse, logout revoke all on password reset / account delete |
| CSRF | Double-submit `ac_csrf` + `X-CSRF-Token`; Bearer exempt; webhooks and public share exempt |
| XSS | No tokens in JS storage; CSP/frame headers on API and Next |
| SQLi | SQLAlchemy bound parameters only |
| IDOR | `owned_assignment` / `owned_document` + `user_id` on jobs/reports/payments |
| Lockout | 8 failures → 15 minute `locked_until` |
| Docs | Env-gated |
| Rate limit | Redis |
| Encryption | Fernet field-level; `FIELD_ENCRYPTION_KEY` required in production |
| Uploads | Extension + magic + zip bomb + optional ClamAV |
| Headers | nosniff, DENY frame, Referrer-Policy, Permissions-Policy, HSTS in production |
| Prompt injection | Hierarchy wrap + output leak detection + 1000 tests |

OWASP ASVS L2 remaining: verified password policy (complexity beyond length), recovery codes, step-up for billing, security.txt, dependency scanning in CI (add pip-audit / npm audit as P1).

---

## 6. Payment hardening plan

**Checkout (real, no stubs)**

- Stripe: `stripe.checkout.Session.create` with `idempotency_key`, metadata `payment_id`.
- Paystack: `POST https://api.paystack.co/transaction/initialize`.
- Flutterwave: `POST https://api.flutterwave.com/v3/payments`.
- Missing secret → HTTP 503. Success URL does **not** grant entitlements.

**Webhooks**

- Stripe official construct + tolerance.
- Paystack SHA512 of raw body.
- Flutterwave shared hash header.
- Persist `webhook_events.event_id` uniquely; duplicates return 200 and do nothing.
- Grant via `apply_successful_payment` only; `PaymentTransaction.provider_event_id` unique.

**Ledger**

- `payments` + `payment_transactions` + `credit_transactions`.
- Double-charge prevention: monthly idempotency key `sub:{user}:{plan}:{YYYYMM}`.
- Failed invoice → `past_due` (dunning mail is P1).

**Do not launch until**

- Staging charges $1 / ₵1 / ₦100 and the plan row flips only after the webhook.
- Replay of the same event does not stack subscriptions or credits.
- Unsigned body is 400.

---

## 7. AI quality improvement plan

Current engine remains heuristic (deterministic, offline). LLM enhancement is optional and schema-gated.

**Workflow (target)**

1. Question Analyzer — command words, topic, scope, required moves.
2. Thesis Analyzer — contestable claim vs topic label.
3. Argument Analyzer — claim/warrant/evidence gaps.
4. Evidence Analyzer — unsourced specifics.
5. Citation Checker — style + reference alignment (no invented sources).
6. Rubric Checker — criterion coverage, not a grade.

**Malformed output**

`complete_validated_json`: parse → jsonschema → secret/system-leak check → retry → next provider → return `None` and keep heuristic result. Never return raw model text to the client.

**Eval**

- Gold sets in `app/services/ai/eval.py` (expand to 200+ items per analyzer).
- Metrics: precision, recall, F1, FP, FN.
- Dashboard: `GET /api/admin/eval`.
- Gate: do not market “95% AI quality” until citation + thesis F1 ≥ 0.90 on held-out gold.

---

## 8. Scalability plan

| Users | API | Workers | DB | Redis | Notes |
|---|---|---|---|---|---|
| 1k | 2 × 1 vCPU | 2 | single PG | 1 | SQLite forbidden |
| 10k | 4–8 | 8–16 | PG + PgBouncer | HA Redis | queue lag alert 60s |
| 100k | 16+ autoscale | 50+ | primary + replica | cluster | shard object storage by `user_id` prefix |

- Stateless API (cookies, no local job state).
- Cache: public SEO/FAQ in Redis/CDN; never cache private reports.
- Burst: Redis rate limits by role.
- CDN: marketing + fonts only. Documents stay signed and private.

---

## 9. Monitoring plan

**Must-have alerts (P1 wiring)**

| Signal | Threshold | Page |
|---|---|---|
| 5xx rate | >1% / 5m | yes |
| Queue lag | >60s p95 or DLQ >0 | yes |
| Job failure rate | >5% / 15m | yes |
| Payment webhook failures | >0 unsigned or >3 apply errors | yes |
| Extraction failures | >10% / 15m | no (ticket) |
| AI spend | daily token budget 80% | no |

Sentry DSN is already read on boot. Add OpenTelemetry FastAPI/SQLAlchemy/RQ instrumentation next. Structured logs already emit `analysis_completed`, `analysis_failed`, `queue_unavailable`.

---

## 10. Deployment architecture

- **Frontend:** Vercel, rewrite `/api` to Railway/ECS, `COOKIE_SECURE=true`, `APP_WEB_URL` exact origin.
- **API + workers:** Docker. Same image, different command (`uvicorn` vs `rq worker analysis`).
- **DB:** Managed PostgreSQL (RDS/Neon/Supabase). `DATABASE_URL` via secrets. PgBouncer transaction pool.
- **Redis:** managed, TLS.
- **Storage:** Cloudflare R2, SSE, no public bucket ACL.
- **Blue-green:** stand up new API, migrate (expand), switch, contract later.
- **Secrets:** Railway/AWS SM/Vercel env. Never bake into images.
- **DR:** daily snapshots + WAL/PITR; quarterly restore to a scratch project; RPO 5m, RTO 2h target.

---

## 11. Testing architecture

| Layer | Location | Must cover |
|---|---|---|
| Unit | `tests/test_question.py`, `test_analysis_engine.py`, `test_prompt_injection.py`, `test_hardening.py` (time helpers) | parsers, firewall, datetime |
| Integration | `test_api_workflow.py`, `test_hardening.py` | register, login, cookie session, analysis, IDOR, share, webhooks |
| Document security | `test_document_security.py` | EXE, fake PDF, zip bomb |
| E2E | Playwright (P1) | guest check, paid checkout sandbox |
| Perf/load | k6 (P1) | 100 rps health, 20 rps analysis enqueue |
| Chaos | P2 | Redis down → 503 in prod; worker kill → DLQ |

**Testing matrix (required scenarios)**

| Scenario | Automated now | Notes |
|---|---|---|
| Registration | yes | |
| Login / logout | yes / logout API | add cookie logout test P1 |
| Uploads | yes | |
| Analysis (guest + registered) | yes | |
| Thesis / citations / rubric | unit + engine | gold quality still low |
| Payments / failed payments | webhook HMAC tests | live Checkout needs staging keys |
| Webhook replay | unique event_id | add explicit second-post assert P1 |
| Account deletion | API exists | add test P1 |
| Guest flow | yes | |
| Report + PDF | workflow | PDF cookie download P1 |
| Document ownership | yes | |

---

## 12. CI/CD pipelines

`.github/workflows/ci.yml`

1. Backend: ruff, pytest + coverage (current fail-under 55; raise to 90 on critical packages when green).
2. Frontend: `tsc --noEmit`.
3. P1 jobs to add: `pip-audit`, Playwright, `alembic upgrade head` against Postgres service, `actionlint`.

Deploy (P1): GitHub Environment `production` with required reviewers; migrate then rollout; smoke `/api/health`.

---

## 13. Production readiness checklist

- [ ] `APP_ENV=production`
- [ ] `create_all` not executed (confirmed in logs)
- [ ] Alembic 002 applied
- [ ] `JWT_SECRET_KEY` ≥ 32 random bytes
- [ ] `FIELD_ENCRYPTION_KEY` set
- [ ] `ADMIN_BOOTSTRAP_*` used once then rotated/removed
- [ ] Default admin login fails
- [ ] Redis + ≥1 RQ worker
- [ ] `REQUIRE_QUEUE=true`
- [ ] Stripe/Paystack/Flutterwave secrets + webhook secrets
- [ ] R2 bucket private
- [ ] Sentry DSN
- [ ] Backups enabled and restore tested
- [ ] CORS exact frontend origin
- [ ] Cookie Secure + HTTPS
- [ ] OpenAPI 404
- [ ] Rate limit 429 under burst

---

## 14. Launch readiness checklist

- [ ] Staging paid checkout observed in provider dashboards
- [ ] Guest and registered analysis both succeed
- [ ] Tenant isolation suite 100%
- [ ] Share link password + expiry demo
- [ ] Legal: privacy, integrity disclaimer, subprocessors
- [ ] Status page + on-call
- [ ] WCAG 2.2 AA report attached
- [ ] SEO canonical + schema on all public pages
- [ ] Support mailbox and abuse process
- [ ] Incident runbook (below) printed in the ops channel

**Runbook — analysis 5xx**

1. Check `/api/health` and Redis ping.
2. `rq info`; if no workers, scale workers, do not inline in prod.
3. Inspect `analysis_dlq`.
4. If datetime or encryption errors, roll forward (do not disable encryption).

**Runbook — payment not applied**

1. Confirm webhook 200 in provider logs.
2. Lookup `webhook_events.event_id` and `payments.id`.
3. Never manually set `successful` without matching provider event.
4. Re-send webhook from the provider dashboard.

---

## 15. 30-day stabilization plan

Week 1: staging deploy, live $1 checkout all three providers, restore drill, kill default admin probe in CI.  
Week 2: raise coverage on auth/billing/credits to 90%; Playwright guest+auth analysis; axe on `/`, `/check`, `/app/report`.  
Week 3: gold datasets (200/analyzer); wire Sentry alerts; ClamAV sidecar.  
Week 4: load test 10k-user profile; freeze scope; go/no-go review against §14.

---

## 16. 90-day roadmap

Days 31–60: structured analyzers in production with fallback; institution admin; SSO spike; read replica.  
Days 61–90: WebSockets; dunning complete; multi-currency charging (not display FX); WCAG sign-off; 100k-user capacity test.

---

## 17. Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Live keys missing, someone “fakes paid” | M | Critical | Code returns 503; forbid client-side plan flip |
| R2 | SQLite in prod | L | Critical | Health check refuse non-Postgres when `APP_ENV=production` (add P1) |
| R3 | Encryption key loss | M | Critical | Backup key in SM; without key, ciphertext is unreadable |
| R4 | Worker backlog | H | High | Autoscale + 503 rather than inline |
| R5 | Prompt injection | H | High | Firewall + never execute document text |
| R6 | Webhook replay | M | High | Unique event ids |
| R7 | XSS in report HTML | M | High | Cookies HttpOnly; PDF/report escape |
| R8 | Coverage theatre | M | Med | Fail CI on critical packages, not vanity global % |
| R9 | Alembic 001 drop_all | L | Critical | Never downgrade 001 in prod |
| R10 | ClamAV down | M | Med | Prod fail closed when host configured |

---

## 18. Cost estimates (monthly, USD, order-of-magnitude)

| Item | 1k users | 10k users | 100k users |
|---|---|---|---|
| Vercel | 20 | 20–150 | 200+ |
| API/workers | 40 | 250 | 2,000 |
| Postgres | 25 | 120 | 800 |
| Redis | 15 | 60 | 400 |
| R2 | 5 | 40 | 300 |
| Stripe fees | 2.9%+30¢ | same | same |
| LLM | 50–200 | 500–2,000 | 5,000–20,000 |
| Sentry/OTel | 0–30 | 80 | 300 |
| **Total opex (ex LLM spike)** | **~180** | **~1,200** | **~8,000+** |

---

## 19. Engineering effort estimates

| Workstream | Remaining after this pass | Owner |
|---|---|---|
| P0 verification in real staging | 3–5 days | Staff BE + DevOps |
| Alembic 001 rewrite + PG baseline | 3 days | BE |
| Live billing certification | 5 days | BE + finance |
| AI gold sets + analyzer split | 15–20 days | ML/BE |
| Observability dashboards | 5 days | DevOps |
| WCAG + mobile pass | 8 days | FE |
| E2E + 90% critical coverage | 8 days | QA |
| DR restore + runbooks drill | 2 days | DevOps |
| **Calendar to honest go-live** | **6–10 weeks** with 4 engineers | |

---

## 20. Exact code-level refactors required per module

| Module | Required change | Done now? |
|---|---|---|
| `app/seed.py` | Remove hardcoded admin; disable leaked credential; bootstrap env only | Yes |
| `app/core/time.py` | Single UTC helper | Yes |
| `app/services/entitlements.py` | `is_past` / `as_utc`; increment after success; credits fallback | Yes |
| `app/core/cookies.py` + `api/v1/auth.py` + `frontend/lib/api.ts` | Cookie session, CSRF, no localStorage | Yes |
| `app/deps.py` | Read `ac_access`; keep Bearer | Yes |
| `app/main.py` | Docs gate, CSRF middleware, headers, no create_all in prod | Yes |
| `app/core/rate_limit.py` | Redis | Yes |
| `app/core/crypto.py` + document/assignment/report writes | Field encryption | Yes |
| `app/services/billing.py` + `api/v1/billing.py` | Real checkout + official webhooks | Yes |
| `app/services/credits.py` | Reserve/consume/refund/expire | Yes |
| `app/api/v1/analysis.py` + `workers/queue.py` | No inline in prod; DLQ | Yes |
| `app/api/v1/reports.py` | Share password/expiry/audit; SQL page | Yes |
| `app/services/ai/firewall.py` + `structured.py` + `eval.py` | Injection + schema + metrics | Yes |
| `alembic/versions/002_*` | Expand/contract | Yes |
| `.github/workflows/ci.yml` | Lint/test/typecheck | Yes |
| `app/repositories/*` | Extract persistence from remaining fat routes (`assignments`, `documents`, `admin`) | **Not done** — next refactor |
| `app/db/session.py` | Replica bind + PgBouncer-ready pool | Partial (pool only) |
| `services/documents/storage.py` | boto3 R2 | Yes |
| Playwright / k6 / axe | FE verification | **Not done** |

Do not mark the product launch-ready until §13 and §14 are evidenced, not merely coded.
