# Runbook: Redis down

**SEV:** 2 when `REQUIRE_QUEUE` or production (ready 503).  
**Owner:** Platform (unassigned). **Alert:** A-REDIS. Local sink once (`ops/cert_alert_fire.json`). PagerDuty **false**.

## Detection

- `/api/ready` 503, JSON `redis: false`
- Enqueue 503; prod rate-limit 503
- After restart, ready may stay 503 for several seconds (recorded +3s still 503)

## Impact

RQ dead. Production auth rate-limit fails closed. Analysis cannot start.

## Mitigation

Keep fail-closed. Do not switch `REQUIRE_QUEUE` off in production to “go green.”

## Recovery

1. Restart Redis (AOF in prod compose — confirm `appendonly` if using that file).
2. Confirm `PING`, then `/api/ready` 200.
3. Workers re-register; check `academiccheck_workers` / `queue_depth`.
4. Stuck jobs: `worker-failure.md` (OPS-07).

## Escalation

SEV-2. SEV-1 if Redis data loss takes the queue and billing rate-limit together during a payment incident.

## Validation

Ready 200. Login not 503. Queue depth finite.

## Postmortem

SEV-2: yes. Note local-only page if that is how it was seen.
