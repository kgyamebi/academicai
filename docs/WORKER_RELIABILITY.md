# Worker reliability

Production queue: Redis + RQ queue `analysis`, DLQ `analysis_dlq`, retry 3× (15s / 60s / 180s).  
`REQUIRE_QUEUE=true` or production env returns 503 if no live worker is registered.

## What is proven in CI

`enqueue_analysis` returns false when Redis is absent (fail closed). Poison jobs log without crashing the process.

## What is not proven

1 / 5 / 10 workers processing 1000 queued jobs, lost-job, duplicate-job, and stuck-job measurements require a staging Redis cluster. Run:

```bash
python ops/queue_load.py --jobs 1000 --workers 1
```

Do not treat this document as a Worker Reliability Certificate until that command is run and the printed lost/duplicate counts are zero.
