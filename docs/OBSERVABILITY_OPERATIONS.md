# Observability Operations — AcademicCheck AI

Date: 2026-09-07  
Companion (logging / tracing / dashboard table): `docs/OPERATIONS_DASHBOARDS.md`.  
Score remains **70 / 98**. Dashboards below are **operating contracts**. Grafana JSON in `ops/grafana/` is import-only. Prometheus server, Grafana, and PagerDuty are **not running**.

Host CPU / memory / disk / network: **not emitted by the app**. Need a node exporter (absent). Do not tick those alerts as validated.

Every dashboard lists owner (vacant), purpose, alert ids from `docs/ALERT_CATALOG.md`, and runbooks.

## Infrastructure

- **Owner:** Platform (unassigned)
- **Purpose:** Process up vs dependency health
- **Signals:** `/api/live`, `/api/ready`, `academiccheck_ready`
- **Alerts:** A-READY, A-DB, A-REDIS (`docs/ALERT_CATALOG.md`)
- **Runbooks:** `docs/RUNBOOK_LIBRARY/redis-failure.md`, `database-failure.md`, `high-error-rate.md`
- **Grafana file:** `ops/grafana/infrastructure.json` (not deployed). Combined view: `operations.json`.

## Database

- **Owner:** Data (unassigned)
- **Purpose:** Connectivity and timeout class failures
- **Signals:** `academiccheck_database`; ready JSON `database`
- **Alerts:** A-DB
- **Runbooks:** `docs/RUNBOOK_LIBRARY/database-failure.md`, `backup-failure.md`, `restore-failure.md`
- **Grafana file:** `ops/grafana/database.json` (not deployed)
- **Host disk for PG data:** **unmonitored**

## Queues / workers

- **Owner:** Backend (unassigned)
- **Purpose:** Analysis pipeline liveness
- **Signals:** `academiccheck_queue_depth`, `academiccheck_workers`
- **Alerts:** A-WORKER, A-QUEUE (`docs/ALERT_CATALOG.md`)
- **Runbooks:** `docs/RUNBOOK_LIBRARY/worker-failure.md`, `queue-backlog.md`
- **Grafana files:** `ops/grafana/workers.json`, `queues.json`, `analysis.json` (not deployed)

## Storage

- **Owner:** Platform (unassigned)
- **Purpose:** Upload path
- **Signals:** Application 400s; `guest_purge_storage_failed` logs; S3 circuit
- **Alerts:** A-STORAGE — **cannot fire**
- **Runbooks:** `docs/RUNBOOK_LIBRARY/storage-failure.md`
- **Grafana file:** `ops/grafana/storage.json` (incomplete; not deployed)
- **Chaos:** `storage_kill` not_run

## Billing

- **Owner:** Payments (unassigned)
- **Purpose:** Webhook and checkout integrity
- **Signals:** `billing.webhook_unmatched`, HTTP 4xx/5xx; PSP dashboards (no keys here)
- **Alerts:** A-WH; A-PAY incomplete (`docs/ALERT_CATALOG.md`)
- **Runbooks:** `docs/RUNBOOK_LIBRARY/billing-failure.md`, `payment-webhook-failure.md`
- **Grafana file:** `ops/grafana/billing.json` (not deployed)

## AI systems

- **Owner:** AI (unassigned)
- **Purpose:** Provider circuits vs heuristic fallback
- **Signals:** `academiccheck_circuit`, `jobs.failed`
- **Alerts:** A-AI
- **Runbooks:** `docs/RUNBOOK_LIBRARY/ai-provider-failure.md`
- **Grafana file:** `ops/grafana/ai.json` (not deployed)

## Security

- **Owner:** Security (unassigned)
- **Purpose:** Auth abuse and 4xx
- **Signals:** `security_events`, `http.4xx`, refresh_reuse
- **Alerts:** A-AUTH (logs); A-WH
- **Runbooks:** `docs/RUNBOOK_LIBRARY/security-incident.md`, `authentication-failure.md`
- **Grafana file:** `ops/grafana/security.json` (not deployed)

## Business metrics

- **Owner:** Product/ops (unassigned)
- **Purpose:** Checks completed, checkout starts — **not a warehouse**. Use `analytics_events` and payment rows in admin SQL with care (no assignment text).
- **Alerts:** None dedicated (`docs/ALERT_CATALOG.md`)
- **Runbooks:** `docs/RUNBOOK_LIBRARY/billing-failure.md` if conversion is money-wrong rather than “low traffic”
- **Grafana file:** `ops/grafana/business.json` (not deployed)

## Alert delivery / escalation / closure

Validated: local HTTP POST on ready 503 (`ops/cert_alert_fire.json`, 1 event).  
Not validated: Grafana, Alertmanager, PagerDuty, ack, escalate, resolve, close.

See `docs/ALERT_VALIDATION_REPORT.md`. Alertmanager rules spec (not loaded): `ops/prometheus/alert-rules.yml`.
