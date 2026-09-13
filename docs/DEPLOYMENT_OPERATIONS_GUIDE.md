# Deployment Operations Guide — AcademicCheck AI

Date: 2026-09-07  
Evidence report (pass/fail): `docs/DEPLOYMENT_OPERATIONS_REPORT.md`.  
Readiness remains **82 / 98**. This guide documents **intended** procedures. Modes marked Fail were **not run**.

Health gate for every procedure: `GET /api/ready` returns 200. `/api/live` staying 200 during Redis/Postgres death is **by design** (`ops/cert_chaos_results.json`). Do not put live on the load balancer.

Monitoring during deploy: `/api/metrics` + ready probe. Grafana JSON is import-only (`docs/OPERATIONS_DASHBOARDS.md`).

---

## Blue-green

| | |
| --- | --- |
| Procedure | Stand up green beside blue. Probe green `/api/ready`. Shift traffic. Keep blue until soak. |
| Validation | Local proxy: `ops/cert_bluegreen_results.json` — green 20/20, kill green, traffic back to blue, 0 errors. |
| Monitoring | Ready, 5xx counter, queue depth on **each** color (process-local). |
| Recovery | Shift back to blue. Image pin required in real CD (absent). |
| Status | **Partial** — workstation proxy. Nginx/Traefik/cloud LB **not run** (OPS-18). |

## Rolling

| | |
| --- | --- |
| Procedure | Replace one replica at a time behind a ready-checking LB. Workers rolling separately from API. |
| Validation | **Not run.** Compose is `api` + `worker`, not a replica set. |
| Monitoring | `academiccheck_workers` must not sit at 0 through the whole roll if `REQUIRE_QUEUE=true`. |
| Recovery | Pause the roll; restart last good replica. |
| Status | **Fail — not run** (OPS-19). |

## Canary

| | |
| --- | --- |
| Procedure | Send a fixed percent of traffic to the new SHA. Abort if 5xx or ready fail vs baseline. |
| Validation | **Not run.** No canary controller. |
| Monitoring | Compare canary vs baseline 5xx/latency. Process-local metrics **cannot** do a correct global rate without Prometheus. |
| Recovery | 0% canary (shift off). |
| Status | **Fail — not run**. |

## Rollback (application)

| | |
| --- | --- |
| Procedure | Previous image/color. Do not “roll forward” a broken billing SHA. |
| Validation | Local automatic rollback in the blue-green cert. GHA `deploy-rollback-drill.yml` **exits 1** without `STAGING_URL`. |
| Monitoring | Ready 200 on the old color; webhook unmatched not spiking. |
| Recovery | If both colors bad: incident + restore from last known-good backup (data path). |
| Status | **Partial**. |

## Migration rollback

| | |
| --- | --- |
| Procedure | Restore `pg_dump` to **scratch**, `ops/validate_restore.py`, then cut over. |
| Validation | Local restore audit RTO ~21 s on cert Postgres — not production, `managed_postgres: false`. |
| Monitoring | Row counts vs dump; payments/credits tables consistent with PSP (PSP keys absent). |
| Recovery | If scratch validate fails, keep primary; do not overwrite. |
| Status | **Fail as certified prod procedure.** Specified only. **Never** `alembic downgrade` on tenant data. |

## Health gates

| Gate | Must pass | Must not be used as |
| --- | --- | --- |
| `/api/ready` | 200 before traffic shift | — |
| Workers ≥ 1 | When `REQUIRE_QUEUE` or production | Optional in local sqlite tests |
| CI pytest floors | 70 overall / 75 billing+isolation | A 90% coverage claim |
| Image scan | **Not run** | A security certificate |

## Release gates (cannot pass today)

Live billing artifact, managed PITR artifact, pentest, named on-call, hosted alerts. See `docs/CTO_PRODUCTION_GATES.md`. Do not mark LAUNCH APPROVED.
