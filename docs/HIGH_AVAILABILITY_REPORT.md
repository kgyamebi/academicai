# High Availability Report — AcademicCheck AI

Date: 2026-09-07

| Architecture claim | In repo | Validated? |
| --- | --- | --- |
| Multiple API instances | HTTP cert: 4 uvicorn workers; horizontal: 2 processes round-robin | p95 miss; nginx **not_run** |
| Multiple workers | prod compose `deploy.replicas: 2` (**Compose ignores this unless Swarm**) | 5 workers in RQ cert; not compose HA |
| Database failover readiness | PITR.md; no replica | **FAIL** |
| Load balancer | ready healthcheck in prod compose | Cloud LB **not_run**; local blue-green proxy |
| Zero SPOF | PG, Redis, disk, region | **FAIL** — SPOFs remain |
| Automatic recovery | `restart: unless-stopped` on prod compose (this pass) | **Not chaos-tested** |

## Instance / worker / DB restart (existing drills)

| Failure | Result |
| --- | --- |
| API green kill | Local proxy rollback, 0 HTTP errors (`cert_bluegreen_results.json`) |
| Worker kill | 1/12 stuck |
| Database process restart | ready 503 → 200 |

## Verdict

**FAIL** high-availability certification. Multi-process local HTTP is not multi-AZ HA.
