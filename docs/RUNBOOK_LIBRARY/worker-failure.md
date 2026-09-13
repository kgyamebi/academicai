# Runbook: Worker crash

**SEV:** 2 if workers = 0 with `REQUIRE_QUEUE`.  
**Owner:** Backend (unassigned). **Alert:** A-WORKER (`academiccheck_workers` = 0). Unwired.  
**Evidence:** `ops/cert_worker_death.json` — 11/12 recovered, **1 queued stuck**.

## Detection

- Metrics `workers` = 0 or enqueue 503
- Jobs stay `queued`/`running` past SLA
- User reports analysis never completing

## Impact

New analysis blocked or hung. Guest purge also stalls (OPS-09).

## Mitigation

Do not duplicate-enqueue the same document blindly. Do not mark jobs successful in SQL.

## Recovery

1. `python -m app.workers.rq_worker` (or compose `worker`).
2. Confirm registered workers ≥ 1.
3. Stuck after SIGKILL: wait for 900s `reap_stale_jobs` or fail via poison path (`record_poison_job`).
4. Inspect Redis RQ failed registry; logs `poison_analysis_job`.

## Escalation

SEV-2. If queue depth grows, also `queue-backlog.md`.

## Validation

A new analysis job reaches terminal success/fail. Depth not monotonically increasing.

## Postmortem

SEV-2: yes. Attach worker-death artifact if a drill.
