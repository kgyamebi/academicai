# Reliability Gap Report — AcademicCheck AI

Date: 2026-09-07  
Reliability score remains **93 / 98**. Gate 98. **FAIL.**  
This pass did **not** re-run 50k jobs, PITR, or hosted Grafana. Unrun = FAIL.

| Requirement | Evidence | Classification |
| --- | --- | --- |
| Backups | Local `pg_dump` restore matched 100k/1M (`cert_restore_audit.json`) | PARTIAL |
| Recovery / PITR | `managed_postgres: false`; WAL replay not exercised | FAIL (managed) |
| Queue processing | 1000 analysis 0 lost; 5k–50k **analysis** unrun | PARTIAL |
| Workers | RQ + SIGTERM; SIGKILL **1 stuck** | FAIL vs zero-stuck |
| Failover | Redis/PG chaos: live 200, ready 503, recover 200 | PARTIAL (two deps) |
| Retries | RQ Retry 3× 15/60/180 | PASS (code + 1000 job) |
| Dead letter | `analysis_dlq` + poison mark | PASS (pytest; 1000 job DLQ 0) |
| Health checks | `/api/live`, `/api/ready` | PASS (chaos + pytest) |
| Stuck jobs | Reaper 900s; kill drill stuck=1 | FAIL |
| Guest file retention | Purge on reaper | PARTIAL (needs worker) |
| Deployment safety | Local proxy blue-green only | FAIL (cloud) |
| Monitoring / alerting | Spec + 1 local 503 POST; no Grafana/PD | FAIL (hosted) |
| HA / no SPOF | Single PG, Redis, disk | FAIL |
| Compose process restart | `restart: unless-stopped` on prod compose (2026-09-07) | **Specified, not chaos-tested** |

## SPOFs

Postgres primary, Redis, local disk/object bucket, single region, vacant on-call, process-local circuits/cache/metrics.

## Race / deadlock / cascade (code vs drilled)

| Issue | Status |
| --- | --- |
| Duplicate webhook apply | Pytest blocks second `event_id` |
| Duplicate RQ `job_id` | `DuplicateJobError` / fetch existing |
| Parallel refresh sessions | Residual (R11) — **not newly proven** |
| DB deadlocks | `lock_timeout=10s`; **deadlock load not injected** |
| Failure cascade | Ready 503 fail-closed on Redis/PG; enqueue false — **PASS** those two. Storage/AI/billing cascade **unrun** |
| Queue starvation | Depth metric; age **not emitted**; 50k unrun |

## Data-loss risks still open

No managed PITR, plaintext dumps, object bytes not in dump, guest purge depends on workers, SIGKILL stuck job until 900s reaper.
