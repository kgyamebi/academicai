# Deployment Recommendation — AcademicCheck AI

Date: 2026-09-07

## Recommendation

**Do not deploy to production for paid or real-student traffic.**

Reliability 93 is **in-repo + Docker laboratory**. It is not 98, not 99.95% uptime, and not zero SPOF.

## May deploy (non-prod)

Staging **after** `STAGING_URL` exists, `/api/ready` is the LB probe, `REQUIRE_QUEUE=true`, and secrets are not sqlite.

## Must exist before production

1. Managed Postgres PITR drill artifact (`managed_postgres: true`)
2. Worker-death re-drill with stuck=0 **or** documented 900s reaper SLO accepted by the business
3. Object-storage backup/restore
4. Live PSP staging certification
5. Hosted alerts that page a named human
6. Compose/K8s restart + LB proven, not only `restart: unless-stopped` in YAML

## Must not claim

Near-zero job loss (kill drill), near-zero data loss (no PITR/objects), self-healing (restart policy untested), high availability (SPOFs remain).
