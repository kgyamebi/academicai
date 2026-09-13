# Security Monitoring Report — AcademicCheck AI

Date: 2026-09-09  

## Events emitted

`login_failed`, `login_success`, `login_locked`, `account_lockout`, `login_new_ip`, `refresh_reuse`, `authorization_denied`, `session_limit_enforced`, webhook/metrics counters, alerting webhook/file/PagerDuty payload.

## Dashboards

In-repo Grafana JSON exists for ops metrics — **not** a dedicated SOC threat dashboard with hosted scrape (HAL-10/11).

## Alerts

Payment/worker/backup/5xx/unhandled via `alerting.py` — proven to file/webhook in certs. Privilege escalation = `authorization_denied` event (no separate pager rule proven).

**PASS** event emission. **FAIL** operated security monitoring / on-call SOC.
