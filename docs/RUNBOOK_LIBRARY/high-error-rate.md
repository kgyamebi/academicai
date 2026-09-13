# Runbook: High error rate

**SEV:** 2 if 5xx > 2% / 5 min (spec, unwired); 1 if errors are billing/auth isolation failures.  
**Owner:** API (unassigned). **Alert:** A-5XX. Unwired.

## Detection

- `http.5xx` / `http.requests` (process-local — **not** a global rate without Prometheus)
- `/api/ready` 503 (A-READY) — often deps, not app bugs
- Logs `unhandled_error` + `request_id`

## Impact

User actions fail. Client errors stay `{error,status}` without traceback.

## Mitigation

LB stays on ready. Do not return stack traces. Do not “retry webhook” storms.

## Recovery

1. Classify: ready 503 → database/redis runbooks.
2. 500s with ready 200 → app/deploy; consider rollback (`deployment-failure.md`).
3. Bind logs by `request_id`. Workers: `job_id` (OPS-25).

## Escalation

SEV-2. Security if 5xx correlate with IDOR attempts (`security-incident.md`).

## Validation

`http.5xx` rate falling. User errors still generic.

## Postmortem

SEV ≥ 2. Request ids, not payloads.
