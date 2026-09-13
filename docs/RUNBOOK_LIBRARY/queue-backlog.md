# Runbook: RQ queue backlog

**SEV:** 2 if depth high and not draining; age **is not emitted** (A-QUEUE is depth-only).  
**Owner:** Backend (unassigned).  
**Evidence:** Queue cert 1000 jobs 0 lost/dup (`ops/cert_queue_results.json`) — that was a drain test, not a page.

## Detection

- `academiccheck_queue_depth` rising
- Users wait on analysis
- Spec wanted age > 10 min — **no series exists**

## Impact

Latency to results. Credit/check consumption may still occur when jobs later run — do not refund in SQL.

## Mitigation

Stop extra enqueue storms (scripts, retries). Keep `REQUIRE_QUEUE=true` in prod.

## Recovery

1. Confirm Redis + workers up.
2. Scale worker replicas (compose/K8s **unrun** for autoscaling).
3. AI circuit open is OK — heuristic still runs; do not disable the worker.
4. Poison jobs: failed registry + `jobs.failed` counter.

## Escalation

SEV-2. If Redis is the cause, `redis-failure.md` first.

## Validation

Depth trending down. New jobs complete.

## Postmortem

SEV-2 if user-visible delay > 30 min or paid checks stuck.
