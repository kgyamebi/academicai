# Service Resilience Report — AcademicCheck AI

Date: 2026-09-07  
Also: `docs/RELIABILITY_CERTIFICATION.md`, `docs/CHAOS_ENGINEERING_REPORT.md`.

| Dependency | Restart / kill | Live | Ready | Recovered | Artifact |
| --- | --- | --- | --- | --- | --- |
| API process | Local blue-green kill green | Edge 200 via blue | — | Automatic rollback | `ops/cert_bluegreen_results.json` |
| Redis | compose stop | 200 | 503 | 200 at +8 s | `ops/cert_chaos_results.json` 12:36:39Z |
| Postgres | compose stop | 200 | 503 | 200 | same |
| Worker SIGKILL | 12 jobs | — | — | **1 queued stuck** | `ops/cert_worker_death.json` |
| Object storage | — | — | — | **Not run** | — |
| Network partition | — | — | — | **Not run** | — |
| AI provider | pytest circuit | — | — | Host **not run** | — |
| Payment provider | pytest circuit | — | — | Host **not run** | — |

Timeouts: DB connect 3 s, statement 30 s, Redis 2 s, S3 5/15 s, AI 90 s, PSP 15 s, SMTP 15 s. See `docs/TIMEOUT_AUDIT_REPORT.md`.

**PARTIAL.** Not a 98 resilience certificate.
