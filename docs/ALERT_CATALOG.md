# Alert Catalog — AcademicCheck AI

Date: 2026-09-07  
A row here is a **specified** alert. Specified ≠ firing. Grafana, Prometheus, Alertmanager, and PagerDuty are **not running**. Process metrics are **per replica and lost on restart** (`backend/app/core/metrics.py`).

Rules (not loaded): `ops/prometheus/alert-rules.yml`.  
Validation: `docs/ALERT_VALIDATION_REPORT.md`.  
Routing (design): `docs/ONCALL_OPERATIONS_GUIDE.md`.

On-call destination: **unassigned** until HAL-11.  
**Basic webhook alerting (no Grafana):** `backend/app/core/alerting.py` → `ALERT_WEBHOOK_URL` / `ALERT_SINK_FILE`.  
Deliberate fire proof: `docs/ALERTING_VERIFICATION.md`, `ops/cert_alerting_proof.json`.

Trigger / ack / escalate / resolve columns for Prometheus rules remain **intended**. Webhook path below is **proven locally**.

| ID | Alert | Signal in repo | Trigger (spec) | SEV | Ack / escalate / resolve (design) | Runbook |
| --- | --- | --- | --- | --- | --- | --- |
| A-READY | API not ready | `academiccheck_ready` = 0 | 2 consecutive scrapes | 2 (1 if data/money) | Ack SEV-2 window; escalate backup; resolve when ready=1 | `high-error-rate.md` |
| A-5XX | API errors | `http.5xx` + `note_http_5xx` webhook | > threshold in window (default 5/60s) **or** Prometheus >2%/5min spec | 2 | Webhook path proven locally | `high-error-rate.md` |
| A-LAT | Latency breach | `academiccheck_http_latency_ms{quantile="0.95"}` | Design p95 `/api/live` < 200 ms — **not a 7-day SLO** | 2 | Same | `high-latency.md` |
| A-CPU | CPU usage | **Not emitted** | n/a | — | Cannot | none |
| A-MEM | Memory usage | **Not emitted** | n/a | — | Cannot | none |
| A-DISK | Disk usage | **Not emitted** | n/a | — | Cannot | `backup-failure.md` (inferred) |
| A-DB | Database failure | `academiccheck_database` = 0 | ready 503 | 1–2 | Local chaos proven; pager unwired | `database-failure.md` |
| A-DBSAT | Database saturation | **Not emitted** (no postgres_exporter) | connections/locks/disk | 2 | Cannot | `database-failure.md` |
| A-REDIS | Redis failure | `academiccheck_redis` = 0 | ready 503 when require_queue/prod | 2 | Local sink once | `redis-failure.md` |
| A-WORKER | Worker failure | `notify_worker_failure` + gauges | job crash / DLQ | 2 | Webhook proven | `worker-failure.md` |
| A-QUEUE | Queue backlog | `academiccheck_queue_depth` | depth > 100 / 10 min. **Age not emitted** | 2 | Unwired | `queue-backlog.md` |
| A-STORAGE | Storage failure | **No gauge** | n/a | 2 | Cannot page | `storage-failure.md` |
| A-PAY | Payment failure | `billing.failed_payments` + `notify_payment_failure` | webhook on fail/signature/unmatch; Prometheus >10/5min spec | 1 | Webhook proven; keys may be absent | PSP runbooks |
| A-WH | Webhook failure | `billing.webhook_unmatched` + payment alert | unmatched actionable event | 1–2 | Webhook proven | `payment-webhook-failure.md` |
| A-AI | AI failure | circuit / `ai.provider_fail` | open or fail > 10% enhanced jobs | 3 | Unwired | `ai-provider-failure.md` |
| A-AUTH | Authentication failure | `security_events` / logs | mass 401 or any `refresh_reuse` | 1 if mass | Logs only | `authentication-failure.md` |
| A-CERT | Certificate expiry | **Not emitted** | 14 days | 2 | Cannot | `certificate-expiry.md` |
| A-BACKUP | Backup failure | `notify_backup_failure` from `ops/backup_postgres.sh` | dump fail / missing DATABASE_URL | 1 | Webhook proven when `ALERT_*` set | `backup-failure.md` |
| A-NET | Host network | **Not emitted** | n/a | — | Cannot | `dns-failure.md` |

SLO design targets (not measured over 7/30/90 days): `docs/ALERTS_AND_SLOS.md`.  
Uptime window measured: **60 s** (`ops/cert_uptime_window.json`).
