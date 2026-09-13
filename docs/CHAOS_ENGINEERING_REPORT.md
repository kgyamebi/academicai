# Chaos Engineering Report — AcademicCheck AI

Date: 2026-09-09  

| Experiment | Result | Artifact |
| --- | --- | --- |
| Redis down → ready 503 → recover | PASS | `ops/cert_chaos_results.json` (2026-09-07) |
| Postgres down → ready 503 → recover | PASS | same |
| Redis docker restart AOF retained | PASS | `ops/cert_redis_restart.json` (2026-09-09) |
| DB delete/DROP/destroy restore | PASS | `ops/cert_restore_audit.json` |
| Local storage delete/corrupt restore | PASS | `ops/cert_storage_recovery.json` |
| Circuit open (AI/S3/PSP/SMTP) | PASS pytest | `test_reliability_hardening.py` |
| storage_kill / AI kill / billing kill | **not_run** | chaos JSON |
| Network latency / loss / partition | **not_run** | |
| Email live failure | **not_run** | |

**PARTIAL PASS** process-level chaos. **FAIL** full chaos engineering certification.
