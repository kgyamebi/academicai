# Failure Recovery Checklist (Public Free Launch)

Use with `docs/LAUNCH_RECOVERY_RUNBOOK.md`. Billing/PSP recovery is out of scope for this launch.

## Detect

| Signal | Where | Action |
|--------|--------|--------|
| `/api/live` 5xx | LB / uptime | Page on-call; restart API |
| `/api/ready` 503 | Ready probe | Check Postgres, Redis, worker policy |
| Sentry spike | Sentry | Triage by release + route |
| Queue depth rising | Worker metrics / Redis | Scale or restart RQ workers |
| Upload failures | Sentry + logs | Storage circuit / ClamAV / disk |

## Stabilize

1. Confirm blast radius (guest check vs authenticated vs admin).
2. Fail closed — never fake a completed analysis or paid state.
3. If analysis broken: keep marketing pages up; show honest error on `/check`.
4. If DB down: site may stay up but `/api/ready` must stay 503.

## Recover

1. Restore dependency (DB/Redis/storage/worker).
2. Drain/retry failed jobs only when safe (idempotent analysis).
3. Smoke: register → check → report → dashboard → prior report.
4. Post brief status to users if outage &gt; 30 minutes.

## Verify

- [ ] `/api/live` and `/api/ready` green
- [ ] One end-to-end check succeeds
- [ ] No infinite loading skeletons on error paths
- [ ] Sentry error rate returning to baseline
