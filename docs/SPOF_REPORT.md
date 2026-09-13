# Single Point of Failure Report

Date: 2026-09-07  
Scope: what was actually running for certification, plus compose intent.

| Component | This cert stack | Redundancy proven? | Residual SPOF |
| --- | --- | --- | --- |
| API | 1–2 local uvicorn processes, no LB | Two processes answered `/api/live` only | Yes — no LB, no multi-AZ |
| Workers | Up to 5 processes on one OS | Throughput scaled 1→5 | Yes — one host; RQ fork only on Linux |
| PostgreSQL | One Docker container, `wal_level=replica` | Dump/restore to a second **database name**, not a replica | Yes — no streaming replica, no failover |
| Redis | One Docker container, AOF | Process restart recovered `/api/ready` | Yes — no Sentinel/Cluster |
| Storage | Local disk | 10k files on one volume | Yes — no R2/S3 replication proof |
| Load balancer | None | — | Yes — missing |
| Secrets | Process env | — | Yes — not a secret manager |

No critical path in this environment is free of a single host or single container.

## Verdict

**Zero-SPOF requirement: FAIL.**
