# Alerting strategy — AcademicCheck AI

## Stack

1. **Sentry** — exceptions (API, RQ worker, browser when `NEXT_PUBLIC_SENTRY_DSN` set).
2. **ALERT_WEBHOOK_URL** — Slack/Discord-compatible JSON (`backend/app/core/alerting.py`).
3. **PagerDuty** — optional routing key for pageable severities.
4. **/api/metrics** + Prometheus text — scrape counters; pair with host alerts.

## What pages a human

| Signal | Severity | Channel |
| --- | --- | --- |
| `/api/ready` failing 2+ minutes | Critical | Webhook + PagerDuty |
| 5xx burst (≥ threshold / window) | High | Webhook |
| Worker zero registered while `REQUIRE_QUEUE=true` | High | Webhook |
| Checkout/webhook processing failures | High | Sentry + Webhook |
| Upload/extract/PDF job failures spike | Medium | Sentry |
| AI provider circuit open | Medium | Sentry / logs |

## Configuration

```env
SENTRY_DSN=
NEXT_PUBLIC_SENTRY_DSN=
ALERT_WEBHOOK_URL=
ALERT_THROTTLE_SECONDS=120
ALERT_5XX_WINDOW_SECONDS=60
ALERT_5XX_THRESHOLD=5
PAGERDUTY_ROUTING_KEY=
```

## Ownership

Name an on-call before public launch. Soft launch may use a single Slack channel; paid production needs a reachable human within RTO.
