# Alerting verification — AcademicCheck AI

Date: 2026-09-07  
Scope: **basic error/failure alerting** only (webhook + file sink). Not full metrics, tracing, Grafana, Prometheus, or PagerDuty.

## Destination

| Setting | Purpose |
| --- | --- |
| `ALERT_WEBHOOK_URL` | Slack or Discord incoming webhook (JSON POST with `text`/`content`) |
| `ALERT_SINK_FILE` | Append-only JSONL fallback / local proof |
| `ALERT_THROTTLE_SECONDS` | Dedup window per `alert_type:title` (default **120**) |
| `ALERT_5XX_WINDOW_SECONDS` | Rolling window for 5xx spike (default **60**) |
| `ALERT_5XX_THRESHOLD` | Fire when ≥ N 5xx in window (default **5**) |

**This verification** used a local HTTP sink at `http://127.0.0.1:8765/alert` (Slack/Discord-compatible JSON body) plus `ops/alert_inbox.jsonl`. No paid observability platform.

Proof artifact: `ops/cert_alerting_proof.json` (`pass: true`, 7 HTTP deliveries).  
Re-run: `py -3.14 ops/verify_alerting.py`  
Unit tests: `py -3.14 -m pytest backend/tests/test_alerting.py -q` (4 passed).

## Alert types — trigger, delivery, proof

| Alert type | How deliberately triggered | Delivered? | Evidence |
| --- | --- | --- | --- |
| `http_5xx_spike` | Called `note_http_5xx` ×3 with verify threshold=3 | Yes | Inbox after step = 1; sample title `HTTP 5xx spike (3 in 60s)` |
| `payment_failure` | `notify_payment_failure(provider=stripe, reason=verify: forged signature)` | Yes | Sample detail `verify: forged signature`; also wired on invalid signatures / unmatched webhooks / `mark_payment_failed` |
| `worker_failure` | `notify_worker_failure(job_id=job-verify-kill, …)` | Yes | Wired on analysis job crash + dead-letter path |
| `backup_failure` | `notify_backup_failure(error=verify: DATABASE_URL missing / pg_dump failed)` | Yes | Same function called from `ops/backup_postgres.sh` `notify_fail` when `ALERT_*` is set |
| `unhandled_exception` | `notify_unhandled_exception(path=/api/verify-boom, …)` | Yes | Wired in FastAPI global `Exception` handler in `backend/app/main.py` |

## Throttle / fatigue guard

- Key: `{alert_type}:{title}`
- Burst of 20 identical `payment_failure` alerts → **1 delivered**, 19 throttled (`throttle_extra_delivered: 1` in proof)
- Suppressed count is included on the next send as `suppressed_duplicates`

## Sample received payload (from proof)

```json
{
  "alert_type": "http_5xx_spike",
  "title": "HTTP 5xx spike (3 in 60s)",
  "detail": "Latest status=500 path=/api/ready",
  "severity": "critical",
  "suppressed_duplicates": 0,
  "context": {"count": 3, "window_seconds": 60, "path": "/api/ready", "status_code": 500},
  "ts": "2026-09-07T19:37:14Z",
  "text": "[CRITICAL] HTTP 5xx spike (3 in 60s)\nLatest status=500 path=/api/ready\ntype=http_5xx_spike suppressed=0 at=2026-09-07T19:37:14Z"
}
```

## Code map

| Layer | Location |
| --- | --- |
| Central alert module | `backend/app/core/alerting.py` |
| API 5xx + unhandled | `backend/app/main.py` |
| Payment/webhook observe | `backend/app/services/billing.py`, `backend/app/api/v1/billing.py` (no payment logic changes beyond notify calls) |
| Worker / DLQ | `backend/app/workers/tasks.py`, `backend/app/services/analysis/runner.py` |
| Backup script hook | `ops/backup_postgres.sh` |

## What this does **not** cover

- Hosted Grafana / Prometheus / Alertmanager / PagerDuty (HAL-10–11)
- On-call staffing / phone routing
- External Slack/Discord account wiring (set `ALERT_WEBHOOK_URL` in deploy env; local sink proves the same POST contract)

## Gate note

Observability score update covers **basic error/failure alerting** specifically — not full metrics/tracing platforms.
