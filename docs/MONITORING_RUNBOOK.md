# Monitoring Runbook — AcademicCheck AI

## What you can scrape today

- `GET /api/live` — liveness  
- `GET /api/ready` — Postgres + Redis (prod/queue)  
- `GET /api/metrics` — JSON counters, circuits, latency histogram (process-local)  
- `GET /api/metrics/prometheus` — text exposition  
- `X-Request-ID` on responses; structlog `request_id`

## What does not exist

Prometheus server, Grafana, Alertmanager, PagerDuty, Slack, OpenTelemetry traces. Do not claim they do.

## First checks

1. Live 200 / ready 503 → dependency. Postgres, Redis, then workers.  
2. Both down → process or LB.  
3. Queue depth rising, workers 0 → start RQ.  
4. Circuit open for stripe/paystack/s3/smtp/openai → fail-fast is working; fix the provider.

Local alert webhook fired once when ready=503 (`ops/cert_alert_fire.json`). That is not PagerDuty.
