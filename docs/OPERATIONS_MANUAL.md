# Operations Manual — AcademicCheck AI

Date: 2026-09-07  
These procedures are for operators. They are not a staffed on-call roster.

## Escalation (fill names before go-live)

1. On-call engineer (unassigned)
2. Backend / SRE lead (unassigned)
3. Founder / incident commander (unassigned)

Until names and a pager exist, this tree is **documentation only**.

## On-call first 15 minutes

1. Open `/api/live` and `/api/ready` on the affected environment.
2. If live 200 and ready 503: dependency outage. Check Postgres, Redis, workers (`ready.workers`).
3. If live fails: process or load balancer. Roll traffic to last known-good (local drill: `ops/cert_bluegreen.py`; production: restore previous task definition / image).
4. Do not run one-off SQL on production without a backup.

## Database outage

- Symptom: ready 503, `database: false`.
- User messaging: analysis/checkout unavailable; do not fake success.
- Recovery: restore from last dump (`ops/cert_restore_audit.py` pattern; production: `ops/restore_postgres.sh` + `ops/validate_restore.py`).
- RTO measured on Docker restore: ~21 s. Managed PITR RTO **unknown**.

## Data loss / accidental delete

- Restore into a side database first. Compare fingerprints (count/min/max id).
- Proven locally: DELETE 250 assignments then restore recovered 100,005 rows.

## Queue outage

- Enqueue returns false without Redis or workers (fail-closed).
- After worker death, inspect `analysis_jobs` for `queued`/`processing`. Re-enqueue or wait for reaper (900 s). **1/12 jobs stayed queued in the kill drill.**

## AI outage

- Circuits open after consecutive failures; heuristic analysis still runs.
- Live provider kill was **not** executed.

## Billing incident

- Checkout without keys is 503.
- Duplicate webhooks must not double-grant (pytest).
- Live PSP incident runbook cannot be certified without provider keys.

## Security incident

- Rotate JWT and field encryption keys (`ops/rotate-secrets.md`).
- Revoke sessions via logout-all.
- Independent pentest still **not** done.

## Disaster recovery

See `docs/DISASTER_RECOVERY_DRILL_REPORT.md`. Full multi-service loss including object storage was **not** drilled.
