# Service Catalog — AcademicCheck AI

Date: 2026-09-07  
Owners and backups are **roles to fill**, not people. Until named, escalation is documentation only (OPS-01).

Criticality: **P0** paid/data path · **P1** core product · **P2** adjacent.

Alerts: `docs/ALERT_CATALOG.md` (specified, mostly unwired).  
Runbooks: `docs/RUNBOOK_LIBRARY/`.  
Dashboards: `docs/OPERATIONS_DASHBOARDS.md` (Grafana JSON not deployed).

---

## Public web (Next.js)

| Field | Value |
| --- | --- |
| Purpose | Student/lecturer UI; rewrites `/api/*` to the FastAPI backend |
| Dependencies | API |
| Owner / backup | Unassigned (frontend) / Unassigned |
| Criticality | P1 |
| Failure impact | App and marketing unusable; API may still serve |
| Alerts | None app-emitted (host/CDN/cert monitors absent) |
| Runbook | `dns-failure.md`, `certificate-expiry.md`, `high-error-rate.md` |
| Recovery | Prior frontend image / platform rollback |

---

## API (FastAPI / uvicorn)

| Field | Value |
| --- | --- |
| Purpose | HTTP product: auth, documents, analysis enqueue, reports, billing webhooks |
| Dependencies | PostgreSQL, Redis (production / `REQUIRE_QUEUE`), secrets, storage |
| Owner / backup | Unassigned (backend) / Unassigned |
| Criticality | P0 |
| Failure impact | All HTTP product down if process dead. `/api/live` may stay 200 if only deps fail (by design) |
| Alerts | A-READY, A-5XX, A-LAT |
| Runbook | `high-error-rate.md`, `high-latency.md`, `deployment-failure.md` |
| Recovery | Restart task; last good image; LB **must** use `/api/ready` |

---

## RQ worker `analysis`

| Field | Value |
| --- | --- |
| Purpose | Run analysis jobs from Redis RQ |
| Dependencies | Redis, PostgreSQL, object storage, optional AI providers |
| Owner / backup | Unassigned (backend) / Unassigned |
| Criticality | P0 |
| Failure impact | New analysis 503 when `REQUIRE_QUEUE=true`; SIGKILL can stick a job 900s (OPS-07) |
| Alerts | A-WORKER, A-QUEUE |
| Runbook | `worker-failure.md`, `queue-backlog.md` |
| Recovery | `python -m app.workers.rq_worker`; reaper; do not double-enqueue |

---

## PostgreSQL

| Field | Value |
| --- | --- |
| Purpose | System of record (users, assignments, reports, billing rows) |
| Dependencies | Disk, backups (`ops/backup_postgres.sh`), optional PgBouncer |
| Owner / backup | Unassigned (data) / Unassigned |
| Criticality | P0 |
| Failure impact | `/api/ready` 503; data loss if volume gone. PITR **not proven** |
| Alerts | A-DB (ping only). A-DBSAT / A-BACKUP **not emitted** |
| Runbook | `database-failure.md`, `data-corruption.md`, `backup-failure.md`, `restore-failure.md` |
| Recovery | Scratch restore via `ops/restore_postgres.sh` + `ops/validate_restore.py`. Never `alembic downgrade` on tenant data |

---

## PgBouncer

| Field | Value |
| --- | --- |
| Purpose | Connection pooling in prod compose |
| Dependencies | PostgreSQL |
| Owner / backup | Unassigned (data) / Unassigned |
| Criticality | P1 |
| Failure impact | Pool exhaustion / auth failures to Postgres |
| Alerts | None dedicated (shows up as A-DB / timeouts) |
| Runbook | `database-failure.md` |
| Recovery | Restart bouncer; API may talk to primary in cert stack |

---

## Redis

| Field | Value |
| --- | --- |
| Purpose | RQ broker, rate-limit backend in production |
| Dependencies | Disk (AOF in prod compose) |
| Owner / backup | Unassigned (platform) / Unassigned |
| Criticality | P0 |
| Failure impact | Queue dead; prod rate-limit 503; ready 503 when `REQUIRE_QUEUE` or production |
| Alerts | A-REDIS. Local sink once (`ops/cert_alert_fire.json`) |
| Runbook | `redis-failure.md` |
| Recovery | Restart Redis; fail-closed enqueue |

---

## Object storage (local / S3)

| Field | Value |
| --- | --- |
| Purpose | Assignment file bytes |
| Dependencies | Disk or network + keys |
| Owner / backup | Unassigned (platform) / Unassigned |
| Criticality | P1 |
| Failure impact | Upload/download fail; guest purge delayed if workers down (OPS-09) |
| Alerts | A-STORAGE **cannot fire** |
| Runbook | `storage-failure.md` |
| Recovery | Config backend switch; object restore **unrun** |

---

## Stripe adapter

| Field | Value |
| --- | --- |
| Purpose | Checkout session + webhook HMAC → ledger apply |
| Dependencies | `STRIPE_*` secrets, public web success/cancel URLs, webhook endpoint |
| Owner / backup | Unassigned (payments) / Unassigned |
| Criticality | P0 |
| Failure impact | Checkout 503 if key missing (current cert: keys **absent**). Wrong apply = money incident |
| Alerts | A-PAY incomplete; `academiccheck_circuit{name="stripe"}` |
| Runbook | `stripe-failure.md`, `payment-webhook-failure.md` |
| Recovery | Circuit open is fail-closed. Replay webhook. **Never SQL-grant credits** |

---

## Paystack adapter

| Field | Value |
| --- | --- |
| Purpose | Initialize transaction + `x-paystack-signature` webhook |
| Dependencies | `PAYSTACK_*` secrets (cert: absent) |
| Owner / backup | Unassigned (payments) / Unassigned |
| Criticality | P0 |
| Failure impact | Same class as Stripe for GH/NG checkout path |
| Alerts | A-PAY incomplete; circuit `paystack` |
| Runbook | `paystack-failure.md`, `payment-webhook-failure.md` |
| Recovery | Same ledger rules as Stripe |

---

## Flutterwave adapter

| Field | Value |
| --- | --- |
| Purpose | Checkout + `verif-hash` webhook |
| Dependencies | `FLUTTERWAVE_*` secrets (cert: absent) |
| Owner / backup | Unassigned (payments) / Unassigned |
| Criticality | P0 |
| Failure impact | Same class as Stripe for FLW checkout path |
| Alerts | A-PAY incomplete; circuit `flutterwave` |
| Runbook | `flutterwave-failure.md`, `payment-webhook-failure.md` |
| Recovery | Same ledger rules as Stripe |

---

## Auth / sessions / JWT

| Field | Value |
| --- | --- |
| Purpose | Register, login, refresh families, CSRF on cookie mutations |
| Dependencies | PostgreSQL, `JWT_SECRET_*`, Redis in production for rate limit |
| Owner / backup | Unassigned (security) / Unassigned |
| Criticality | P0 |
| Failure impact | Login/refresh fail; lockouts; session leak is SEV-0/1 |
| Alerts | A-AUTH logs/`security_events` only |
| Runbook | `authentication-failure.md`, `security-incident.md` |
| Recovery | `JWT_SECRET_PREVIOUS`; `ops/rotate-secrets.md`; revoke families |

---

## AI providers

| Field | Value |
| --- | --- |
| Purpose | Optional enrich/coach. Heuristic analysis is independent |
| Dependencies | Network, API keys, in-process circuit breaker |
| Owner / backup | Unassigned (AI) / Unassigned |
| Criticality | P2 |
| Failure impact | Enrich/coach degrade; core scores still heuristic |
| Alerts | A-AI |
| Runbook | `ai-provider-failure.md` |
| Recovery | Leave circuit open. Do not invent LLM text |

---

## SMTP / email

| Field | Value |
| --- | --- |
| Purpose | Verify / reset mail |
| Dependencies | SMTP host; circuit |
| Owner / backup | Unassigned (ops) / Unassigned |
| Criticality | P2 |
| Failure impact | Verify/reset missing. Console provider in non-prod |
| Alerts | Circuit if used; no dedicated gauge |
| Runbook | `authentication-failure.md` (reset path) |
| Recovery | Console/SMTP circuit; do not log tokens |

---

## CI (GitHub Actions)

| Field | Value |
| --- | --- |
| Purpose | ruff, pytest cov floors, a11y |
| Dependencies | GitHub |
| Owner / backup | Unassigned (devops) / Unassigned |
| Criticality | P2 |
| Failure impact | Merges untested |
| Alerts | GitHub email (platform), not app metrics |
| Runbook | `deployment-failure.md` |
| Recovery | Re-run workflow. `pip-audit` does not block |

---

## Cert / local compose

| Field | Value |
| --- | --- |
| Purpose | Workstation drills only |
| Dependencies | Docker |
| Owner / backup | Unassigned (sre) / Unassigned |
| Criticality | P2 |
| Failure impact | Drills only — not production |
| Alerts | n/a |
| Runbook | `docs/DEPLOYMENT_OPERATIONS_GUIDE.md` |
| Recovery | `docker-compose.cert.yml` |

Fill Owner/Backup **before** paid traffic. Vacant rows remain OPS-01.
