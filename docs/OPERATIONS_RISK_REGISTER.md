# Operations Risk Register — AcademicCheck AI

Date: 2026-09-07  
Rule: every row is from code, compose, CI, or `ops/cert_*.json`. Unrun production ops are not green.  
Operations score remains **58 / 98**. Observability remains **70 / 98**. On-call: **unassigned**. Grafana/PagerDuty/Alertmanager: **not deployed**.

Owners below are **roles**. Named humans do not exist in this repository (OPS-01).

## Summary

| Class | Count | IDs |
| --- | ---: | --- |
| Critical | 6 | OPS-01–OPS-06 |
| High | 10 | OPS-07–OPS-14, OPS-23, OPS-26 |
| Medium | 8 | OPS-15–OPS-20, OPS-24, OPS-25 |
| Low | 2 | OPS-21, OPS-22 |

## Register

### OPS-01 — No named owners or pager — **Critical** — Governance

- **Root cause:** Service catalog and IR plan list vacant seats. No PagerDuty (or equivalent) schedule.
- **Business impact:** A ready-503 or money-wrong event has no accountable responder. MTTA is unbounded.
- **Detection:** Roster review; `docs/SERVICE_CATALOG.md` Owner = Unassigned; `ops/cert_alert_fire.json` `pagerduty: false`.
- **Recovery:** Name primary + backup per service; wire a pager; drill a page-to-ack. Documents alone do not close this.
- **Owner:** Service delivery (unassigned)

### OPS-02 — No production CD — **Critical** — Deployment

- **Root cause:** CI tests only (`.github/workflows/ci.yml`). `deploy-rollback-drill.yml` `exit 1` if `STAGING_URL` unset. No image publish.
- **Business impact:** Production ship is manual and unrehearsed. Rollback in cloud is unproven.
- **Detection:** Absence of a deploy job; GHA drill fail-closed.
- **Recovery:** Staging URL + health gate on `/api/ready`; pin image digest; rehearsed rollback. Local blue-green is not a substitute (`ops/cert_bluegreen_results.json`).
- **Owner:** DevOps (unassigned)

### OPS-03 — Managed PITR absent — **Critical** — Database / DR

- **Root cause:** Restore certification used `pg_dump` into `academiccheck_restore`. `ops/cert_restore_audit.json` `managed_postgres: false`.
- **Business impact:** RPO = last dump only. WAL gap = unrecoverable writes after that dump.
- **Detection:** Restore audit JSON; no provider PITR artifact.
- **Recovery:** Enable provider PITR; restore drill to a **scratch** database; keep `ops/restore_postgres.sh` as the dump path.
- **Owner:** Data (unassigned)

### OPS-04 — Live PSP uncertified — **Critical** — Billing

- **Root cause:** `ops/cert_payment_keys.json` — Stripe/Paystack/Flutterwave secrets all false; `live_charges_executed: false`.
- **Business impact:** Cannot take paid traffic. Checkout returns 503 when keys missing (`backend/app/services/billing.py`).
- **Detection:** Payment-keys cert; checkout 503; empty secret manager.
- **Recovery:** Load keys in a manager (not git); webhook HMAC round-trip in staging; never SQL-grant credits.
- **Owner:** Payments (unassigned)

### OPS-05 — Secrets not in a manager — **Critical** — Auth / config

- **Root cause:** Env and optional `SECRETS_FILE`. No Vault/AWS SM/GCP SM integration proven.
- **Business impact:** Key leak; rotation under load unproven; JWT dual-key window may be skipped.
- **Detection:** Repo has no manager client; `.env` gitignored (correct) but not a control by itself.
- **Recovery:** Manager + `ops/rotate-secrets.md` drill with `JWT_SECRET_PREVIOUS`.
- **Owner:** Security / platform (unassigned)

### OPS-06 — Hosted alerting unwired — **Critical** — Monitoring

- **Root cause:** Alert rules exist as YAML only (`ops/prometheus/alert-rules.yml`). Prometheus/Alertmanager/Grafana not running.
- **Business impact:** Ready 503 may have no human page. Local sink fired once (`ops/cert_alert_fire.json`).
- **Detection:** `grafana/pagerduty/alertmanager: false` in that artifact.
- **Recovery:** Scrape `/api/metrics/prometheus` per replica; load rules; page on-call; prove ack/resolve/close.
- **Owner:** SRE (unassigned)

### OPS-07 — Worker SIGKILL leaves stuck job — **High** — Queue

- **Root cause:** RQ job not always failed on hard kill. Reaper is 900s (`reap_stale_jobs`).
- **Business impact:** Analysis appears hung; user waits until reaper.
- **Detection:** `ops/cert_worker_death.json` 11/12 recovered, stuck=1.
- **Recovery:** `docs/RUNBOOK_LIBRARY/worker-failure.md`; restart worker; wait or fail via reaper. Do not duplicate enqueue blindly.
- **Owner:** Backend (unassigned)

### OPS-08 — HTTP p95 fails at 100 in-flight — **High** — API

- **Root cause:** Process/DB capacity on the cert host; PDF and ready probes are heavier than `/api/live`.
- **Business impact:** Launch load unknown. SLO p95 < 200 ms is a **design** target, not a 30-day measure.
- **Detection:** `ops/cert_http_results.json` live_100 p95 1129 ms fail; k6 100 VU p95 ~1879 ms.
- **Recovery:** `high-latency.md`; scale workers/replicas; do not claim 1k–50k users.
- **Owner:** Backend (unassigned)

### OPS-09 — Guest purge only when reaper runs — **High** — Storage

- **Root cause:** `purge_expired_guest_documents` is invoked from `reap_stale_jobs` (worker path).
- **Business impact:** Expired guest files linger if workers are down (disk/privacy).
- **Detection:** Code path in `backend/app/services/analysis/runner.py`; no independent cron.
- **Recovery:** Keep workers up; add a scheduled job **outside** analysis (not implemented). Runbook: `storage-failure.md`.
- **Owner:** Platform (unassigned)

### OPS-10 — Image CVE scan not run — **High** — Deployment

- **Root cause:** CI has no Trivy/Grype job. `pip-audit` is non-blocking (OPS-16).
- **Business impact:** Known vulns can ship if/when images exist.
- **Detection:** `.github/workflows/ci.yml` has no scan step.
- **Recovery:** Add a blocking scan on the deploy image (image publish also absent — OPS-02).
- **Owner:** DevOps (unassigned)

### OPS-11 — Account delete does not cancel PSP subscription — **High** — Billing

- **Root cause:** Local subscription set `cancelled`; Stripe/Paystack/FLW cancel API **not** called.
- **Business impact:** Provider may keep charging after account delete.
- **Detection:** Auth/account-delete code path; no PSP cancel in billing service for that flow.
- **Recovery:** Cancel at PSP first, then local; dispute via PSP dashboard (keys absent here).
- **Owner:** Payments (unassigned)

### OPS-12 — Process-local metrics — **High** — Observability

- **Root cause:** `backend/app/core/metrics.py` in-process Counter + 2000-sample latency list.
- **Business impact:** Lost on restart; per replica; PromQL `rate()` is wrong until a real Prometheus histogram exists.
- **Detection:** Code; `/api/metrics` JSON.
- **Recovery:** Sidecar/central metrics. Do not treat process gauges as SLOs.
- **Owner:** SRE (unassigned)

### OPS-13 — No node CPU/mem/disk/net metrics — **High** — Infrastructure

- **Root cause:** App does not emit host gauges. No node_exporter in compose.
- **Business impact:** Host saturation invisible. A-CPU/A-MEM/A-DISK/A-NET **cannot fire**.
- **Detection:** `GET /api/metrics/prometheus` series list; compose files.
- **Recovery:** Deploy node/volume exporters; then load host alert rules.
- **Owner:** Platform (unassigned)

### OPS-14 — Chaos not run for storage/AI/billing/network — **High** — Reliability

- **Root cause:** `ops/cert_chaos_results.json` marks those scenarios `not_run`. Redis/Postgres down **were** run.
- **Business impact:** Failover unknown for those domains.
- **Detection:** Chaos JSON.
- **Recovery:** Run remaining chaos against staging; do not invent results.
- **Owner:** SRE (unassigned)

### OPS-15 — Alembic 001 historical create_all — **Medium** — Database

- **Root cause:** `001_initial.py` uses create/drop patterns unsafe if replayed on prod.
- **Business impact:** Schema drift or wipe if someone runs the wrong revision on a live DB.
- **Detection:** Migration file review.
- **Recovery:** Never `downgrade` through 001 on tenant data; restore dump. Production lifespan skips `create_all`.
- **Owner:** Data (unassigned)

### OPS-16 — pip-audit non-blocking — **Medium** — Change

- **Root cause:** `ci.yml` `pip-audit ... || true`.
- **Business impact:** Dependency CVE can merge.
- **Detection:** Workflow file.
- **Recovery:** Fail CI on high/critical after a baseline is triaged (not done).
- **Owner:** DevOps (unassigned)

### OPS-17 — Offset pagination untested at 5M — **Medium** — Database

- **Root cause:** EXPLAIN/index work stopped at 100k/1M class, not 5M.
- **Business impact:** Deep list latency under large tenants.
- **Detection:** Prior DB reports; no 5M fixture in CI.
- **Recovery:** Keyset pagination or proven indexes before that scale. Not a launch blocker vs OPS-01–06.
- **Owner:** Backend (unassigned)

### OPS-18 — Blue-green is workstation proxy — **Medium** — Deployment

- **Root cause:** Cert used a local proxy, not Nginx/Traefik/cloud LB.
- **Business impact:** Operators may assume cloud LB behavior that was never run.
- **Detection:** `ops/cert_bluegreen_results.json`.
- **Recovery:** Repeat on the real LB. Guide: `docs/DEPLOYMENT_OPERATIONS_GUIDE.md`.
- **Owner:** DevOps (unassigned)

### OPS-19 — Canary / rolling on K8s unrun — **Medium** — Deployment

- **Root cause:** No certified k8s/ECS manifests. Compose `api` + `worker` only.
- **Business impact:** Wrong mental model during an incident.
- **Detection:** Repo layout; no canary controller.
- **Recovery:** Do not claim canary/rolling until a drill exists.
- **Owner:** DevOps (unassigned)

### OPS-20 — Status page / stakeholder comms vacant — **Medium** — Incident

- **Root cause:** No status URL; stakeholder names vacant.
- **Business impact:** Users uninformed in SEV-0/1.
- **Detection:** `docs/INCIDENT_RESPONSE_PLAN.md`.
- **Recovery:** Provision status page; fill names. Until then use the GitHub incident issue.
- **Owner:** Service delivery (unassigned)

### OPS-21 — CI uses SQLite while prod forbids it — **Low** — Change

- **Root cause:** CI `DATABASE_URL: sqlite:///./ci.db`; production lifespan raises on sqlite.
- **Business impact:** Dialect surprises (JSON, concurrency).
- **Detection:** `ci.yml` vs `main.py` lifespan.
- **Recovery:** Optional PG service in CI (not required to close Criticals).
- **Owner:** DevOps (unassigned)

### OPS-22 — RQ vs Celery docs drift — **Low** — Runbooks

- **Root cause:** Worker is RQ (`python -m app.workers.rq_worker`).
- **Business impact:** Operator follows the wrong tool.
- **Detection:** Worker module vs leftover Celery mentions in older docs.
- **Recovery:** This library uses RQ only. Ignore Celery.
- **Owner:** Backend (unassigned)

### OPS-23 — No distributed tracing — **High** — Observability

- **Root cause:** OpenTelemetry is **not installed**. Sentry traces only if `SENTRY_DSN` set (`traces_sample_rate=0.1`); DSN default empty.
- **Business impact:** Cannot follow a request API → Redis/RQ → worker → DB as a trace. Correlation is `X-Request-ID` on HTTP only.
- **Detection:** `docs/OBSERVABILITY_GAP_REPORT.md`; `backend/app/main.py`; `backend/app/workers/tasks.py` does not bind `request_id`.
- **Recovery:** OTel SDK + collector **or** proven Sentry APM. Until then grep logs by `request_id` / `job_id`.
- **Owner:** SRE (unassigned)

### OPS-24 — Sentry DSN unset — **Medium** — Observability

- **Root cause:** `sentry_dsn: str = ""` in config. Init is conditional.
- **Business impact:** Unhandled errors may exist only in stdout JSON (prod) or console (dev).
- **Detection:** Config default; no DSN in cert env.
- **Recovery:** Set DSN from a secret manager in staging first. Do not send assignment text.
- **Owner:** SRE (unassigned)

### OPS-25 — Worker jobs lack HTTP request_id — **Medium** — Observability

- **Root cause:** HTTP middleware binds structlog `request_id`. RQ `run_analysis_job` does not.
- **Business impact:** User-facing request and analysis job logs may not join except via `job_id` in DB.
- **Detection:** `backend/app/workers/tasks.py` vs `backend/app/main.py`.
- **Recovery:** Pass/bind job_id (already logged on poison path). Full trace still needs OPS-23.
- **Owner:** Backend (unassigned)

### OPS-26 — Backup success/failure is not a metric — **High** — Recovery

- **Root cause:** `ops/backup_postgres.sh` writes a gzip file and prints a path. No Prometheus series, no CI schedule proven offsite.
- **Business impact:** Silent backup stop. A-BACKUP **cannot fire**.
- **Detection:** Script; alert catalog A-BACKUP row.
- **Recovery:** Cron/GHA that fails if dump missing/empty + restore validate. Offsite copy unproven.
- **Owner:** Data (unassigned)

## Human bottlenecks

- Vacant on-call (OPS-01).
- Human `pg_dump` / `psql` restore (OPS-03, OPS-26).
- Billing disputes need PSP dashboards this repo does not have (OPS-04).

## Missing automation (not mocked)

Production deploy, PITR restore job, Alertmanager routes, node exporters, image scan gate, scheduled guest purge independent of analysis workers, backup freshness exporter.
