# Reliability Risk Register — AcademicCheck AI

Date: 2026-09-09  
Rule: unrun chaos / live provider / managed HA remain open. Pytest ≠ production reliability.

| ID | Severity | Risk | Area | Treatment | Residual |
| --- | --- | --- | --- | --- | --- |
| REL-01 | Critical | Worker SIGKILL leaves stuck job | Workers | Heartbeat + orphan recover (exactly once) + stale reaper | **Open** — `cert_worker_death.json` stuck=1 (HAL-15) |
| REL-02 | Critical | No managed PITR | Database | Local dump/restore proven | Writes after dump unrecoverable (HAL-05) |
| REL-03 | High | Live AI/PSP kill unrun | Dependencies | Circuits + fail-closed checkout | Live path UNPROVEN (HAL-14/17) |
| REL-04 | High | Redis volume wipe loses RQ payloads | Queue | DB job rows + `recover_jobs.py` | AOF wipe UNPROVEN |
| REL-05 | High | Object bytes not in DB dump | Storage | Local checksum drill | S3/CRR unrun |
| REL-06 | High | Single-region SPOF | Infra | Compose restart policies | Multi-region FAIL |
| REL-07 | Medium | Queue saturation 5k–50k analysis unrun | Queue | 1k analysis historical PASS | Overflow unknown |
| REL-08 | Medium | In-process circuits reset on API restart | Circuit | Fast-fail when open | State not shared across workers |
| REL-09 | Medium | Email send is fire-and-forget | Email | SMTP timeout + circuit | No durable outbox |
| REL-10 | Low | Rate-limit Redis timeout → 503 | API | Fail-closed prod | Flaky if Redis slow |

## SPOFs

Postgres volume · Redis volume · local disk / single bucket · single region · vacant on-call.

## Cascading failure

Redis down → ready 503 (proven 2026-09-07). Postgres down → ready 503. Open AI circuit → heuristic continue (code). Open billing circuit → checkout 503 (pytest).
