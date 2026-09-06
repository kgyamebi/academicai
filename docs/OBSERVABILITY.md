# Observability

## Health

- `GET /api/live` — process up
- `GET /api/health` — shallow status
- `GET /api/ready` — database, and Redis/workers when production or `REQUIRE_QUEUE=true`
- `GET /api/metrics` — health plus in-process counters (`http.requests`, `http.5xx`, `http.4xx`, `billing.successful_payments`)

Structured JSON logs in production via structlog. Sentry initializes when `SENTRY_DSN` is set.

## Dashboards to wire in the host (not invented here)

Use the host metrics backend (CloudWatch, Grafana, Datadog) to graph:

- Operations: 5xx rate, p95 latency, ready=false
- Security: `login_new_ip` and lockout events from `/api/admin/security-events`
- AI: `token_usage` from `/api/admin/overview`
- Billing: successful payments vs webhook duplicates
- Queue: RQ worker count from `/api/ready`

In-process counters reset on deploy. They are not a replacement for Prometheus remote write.
