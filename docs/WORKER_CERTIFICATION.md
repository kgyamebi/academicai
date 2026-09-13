# Worker Certification

Date: 2026-09-07  
Also: `docs/QUEUE_CERTIFICATION.md`, `docs/WORKER_RELIABILITY_CERTIFICATION.md`

| Drill | Result | Artifact |
| --- | --- | --- |
| 1,000 analysis jobs, 5 workers | 1000 completed, 0 lost, 0 duplicate, 0 stuck | `ops/cert_queue_results.json` |
| 5,000 / 10,000 ping | 0 lost | `ops/cert_queue_ping_*.json` |
| 50,000 ping | **not completed** | — |
| Unexpected worker death | 11/12 completed, **1 queued stuck** | `ops/cert_worker_death.json` |
| SIGTERM `request_stop` | Code present | `rq_worker.py` — does not apply to SIGKILL |
| DLQ / poison | `record_poison_job` + fail + refund | pytest |
| Dedup | stable RQ `job_id` | pytest + enqueue |

**PASS** at 1,000 analysis jobs. **FAIL** worker-death zero-stuck and 5k–50k analysis jobs. Not certified for production worker HA.
