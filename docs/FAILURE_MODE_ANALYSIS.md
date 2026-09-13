# Failure Mode Analysis — AcademicCheck AI

Date: 2026-09-09  

| Service | Failure | Root cause | Impact | Detection | Recovery | Automation | Validation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| API | Process crash | OOM / unhandled | 502 until restart | `/api/live`, 5xx alert | Compose `restart` | Yes | Chaos historical |
| Postgres | Instance down | Host/disk | Writes fail; ready 503 | Ready + statement timeout | Restart / restore dump | Partial | Chaos PG down PASS; PITR FAIL |
| Redis | Process down | Host | Queue/rate-limit; ready 503 in prod | Ready | Restart + AOF if volume | Restart yes | Restart PASS; wipe FAIL |
| Worker | Crash mid-job | Kill / exception | Job processing | Heartbeat lag, DLQ | Orphan requeue once, then fail | Yes | Pytest orphan PASS; kill 12/12 FAIL |
| RQ | Poison job | Bad payload | Retry storm risk | DLQ | `record_poison_job` + fail_job | Yes | pytest DLQ |
| Storage | Disk/S3 down | Network/creds | Upload fail | Circuit / OS error | Retry S3 2×; local untested | Circuit pytest | storage_kill not_run |
| AI | Provider 5xx | Vendor | Enrich skipped | Circuit metric | Fallback + heuristic | Yes | Live kill not_run |
| Billing PSP | Timeout | Vendor | Checkout 503 | Circuit + payment alert | No fake paid; webhook retry | Idempotency pytest | Live kill not_run |
| Email | SMTP hang | Vendor | Verify delay | SMTP timeout 15s + circuit | Log; no outbox | Circuit pytest | Live unrun |
| Deploy | Bad image | Human | Ready never 1 | Health gate | `rollback_compose.sh` | Script | Prod CD unproven |

Do not treat this table as a passed chaos campaign.
