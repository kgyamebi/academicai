# Remaining Reliability Risks — AcademicCheck AI

Date: 2026-09-07  
Score **93 / 98** unchanged. External infrastructure required to close Criticals.

| ID | Risk | Needs |
| --- | --- | --- |
| R1 | SIGKILL stuck job | RQ/visibility drill after 900s or job watchdog; re-run `cert_worker_death` |
| R2 | Live PSP uncertified | Keys + staging webhooks |
| R4 | S3 hang/outage | `storage_kill` chaos |
| R6 | No DB failover | Managed replica/PITR drill |
| R7 | Live LLM unrun | `ai_provider_kill` |
| R10 | 50k jobs unrun | Staging Redis volume test |
| R13 | PITR | Provider console restore |
| R14 | No traces | OTel collector |
| OPS-01 | Vacant on-call | Named pager |
| DR-04 | Files not in dump | Object backup |
| S1 | HTTP p95 at 100 in-flight | Capacity, not only reliability |

Compose `restart: unless-stopped` does **not** close R1 (SIGKILL vs restart policy untested together).
