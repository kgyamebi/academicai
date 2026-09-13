# Business Continuity Plan — AcademicCheck AI

Date: 2026-09-09  
This plan is operable as **priorities and vendor steps**. It is **not** a certified BCP: on-call is vacant, PITR is false, S3 object restore is unrun, paid traffic is blocked (no live PSP keys). Local DB/storage/redis restart drills: see `docs/RECOVERY_DRILL_REPORT.md`.

Related: `docs/DISASTER_RECOVERY_RISK_REGISTER.md`, `docs/RECOVERY_OBJECTIVES.md`, `docs/INCIDENT_RESPONSE_PLAN.md`, `docs/RUNBOOK_LIBRARY/`.

## Continuity modes

| Mode | Meaning | Available today |
| --- | --- | --- |
| Fail closed | `/api/ready` 503; no fake analysis success; no SQL credits | **Code yes** (chaos ready 503) |
| Degraded product | Heuristic analysis without LLM | **Code yes**; live AI kill unrun |
| Degraded payments | Checkout 503 if PSP/circuit down | **Code yes**; live PSP unrun |
| Alternate region | Active-active or warm standby | **No** |
| Status communication | Public status page | **No** (incident GitHub issue only) |

## Service recovery priorities

Restore in this order when more than one thing is dead. Do not invert to “fix AI first.”

| Priority | Service | Why | Runbook |
| ---: | --- | --- | --- |
| P0 | Secrets + Postgres | Identity, ledger, assignments | `database-failure.md`, `restore-failure.md`, `data-corruption.md`, `ops/rotate-secrets.md` |
| P0 | Object storage | Upload bytes not in dump | `storage-failure.md` |
| P0 | Auth usability | Login after DB up; Redis if prod rate-limit | `authentication-failure.md`, `redis-failure.md` |
| P0 | Billing webhooks | Money truth is PSP + ledger | `billing-failure.md`, PSP runbooks |
| P1 | Redis + RQ workers | New analysis | `redis-failure.md`, `worker-failure.md`, `queue-backlog.md` |
| P1 | API / web | Users reach the product | `deployment-failure.md`, `dns-failure.md`, `certificate-expiry.md` |
| P2 | AI providers | Enrich only | `ai-provider-failure.md` |
| P2 | SMTP | Verify/reset mail | `authentication-failure.md` |
| P2 | CI | Cannot merge | `deployment-failure.md` |

Analysis without files or DB is not continuity — it is a different product. Do not stand up a “demo” tenant as if it were production.

## Vendor failure procedures

| Vendor class | Examples | Continuity action | Proven? |
| --- | --- | --- | --- |
| Card / PSP | Stripe, Paystack, Flutterwave | Stop checkout; do not SQL-grant; replay webhooks when up | Pytest idempotency only |
| LLM | Configured providers | Leave circuit open; heuristic continues | Code; live unrun |
| Email | SMTP host | Reset/verify delayed; console in non-prod | Unrun |
| DNS / cert | Registrar, CA | `dns-failure.md` / `certificate-expiry.md` | Unrun |
| Object store | S3, R2, Azure Blob | Fail upload; no proven restore | Unrun |
| GitHub Actions | CI | Merge freeze | CI exists; not a DR drill |

## Cloud failure procedures

| Failure | Action | Proven? |
| --- | --- | --- |
| Single VM / compose host | Recreate from image **(no prod image CD)** + restore dump to scratch + attach storage | Image publish **absent** (OPS-02) |
| Postgres instance | Provider PITR to scratch (`ops/PITR.md`) then cut over | **Not executed** |
| Redis instance | New Redis; **jobs lost** unless AOF restored (unproven); re-enqueue from DB jobs if status allows — **no automated replay** |
| Load balancer | Point DNS at last good; health `/api/ready` | Local proxy only |

## Region failure procedures

No second region is declared in this repository. **RTO/RPO for region loss: not measured.**

If a region is later chosen:

1. Postgres: provider cross-region replica or PITR into the new region (must be drilled).
2. Objects: bucket replication (not configured here).
3. Redis: treat as ephemeral; drain/rebuild from DB job state (procedure **not automated**).
4. Secrets: restore from manager in the new region (manager **not proven**).
5. DNS: failover record with tested TTL (unrun).

Until that exists, region loss is **SEV-0** with unbounded RTO.

## Maximum tolerable downtime (business — not measured)

The product has no contractual SLA in-repo. Design API availability 99.9% in `docs/ALERTS_AND_SLOS.md` is **not** a 30-day measurement (uptime window certified: **60 s**).

## When to halt paid traffic

- Ledger/PSP mismatch
- Restore in progress
- Tenant isolation doubt
- Secret leak

Never “keep charging” through an incomplete restore.
