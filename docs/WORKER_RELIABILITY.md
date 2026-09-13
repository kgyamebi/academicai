# Worker Reliability Report

Production queue: Redis + RQ queue `analysis`, DLQ `analysis_dlq`, retry 3× (15s / 60s / 180s).  
`REQUIRE_QUEUE=true` or production env returns not-ready (HTTP 503 on `/api/ready`) if Redis is down.

## Proven in CI

- `enqueue_analysis` returns false when Redis is absent (fail closed).
- Poison jobs log without crashing the process.
- `/api/live` stays 200 when the database is down.

## Not proven

1 / 5 / 20 / 50 workers processing 1000–50000 jobs. Lost-job, duplicate-job, and stuck-job measurements require staging Redis.

```bash
python ops/queue_load.py --jobs 1000 --workers 1
```

Do not treat this document as a Worker Reliability Certificate until that command is run and printed lost/duplicate counts are zero.

DLQ now marks the analysis job `failed` and refunds reserved credits (`record_poison_job` → `fail_job`). Stale `processing`/`queued` jobs older than 15 minutes are reaped. Proven in `tests/test_reliability_failures.py`. Live 1000-job RQ proof is still missing.

In-process heuristic scale 1–25 is in `docs/WORKER_SCALING.md`. That is not an RQ certificate.

**Score contribution: code recovery 88-bound; queue volume still 50. Not load-certified.**
