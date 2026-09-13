# Disaster Recovery Drill Report — AcademicCheck AI

Date: 2026-09-09  
Suite: `ops/cert_dr_repeat.json`.

## Consecutive local runs

| Drill | Run 1 | Run 2 |
| --- | --- | --- |
| Isolated restore from host dump | 43.346 s, counts match | 43.067 s, counts match |
| MinIO integrity | upload 2.943 s, integrity true, prune true | upload 3.023 s, integrity true, prune true |
| WAL PITR | ids 1,2 → **1** | ids 1,2 → **1** |
| Storage app read | checksum + read_bytes | checksum + read_bytes |
| Queue SIGKILL | 12 queued, 0 lost | 12 queued, 0 lost |

Postgres source counts used for restore compare: assignments 100006, findings 1003333.

## Combined prod drill

Not run (needs production credentials).

## Verdict

Local destroy/restore package is repeatable. Production and multi-region remain uncertified.
