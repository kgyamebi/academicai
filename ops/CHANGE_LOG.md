# Production change log

Append one row per production or staging-affecting change. Do not backfill fictional deploys.

| UTC | Env | Change | SHA / image | Alembic | Approver | Result |
| --- | --- | --- | --- | --- | --- | --- |
| — | production | **None.** No production environment is attached to this repository. | — | — | — | n/a |
| 2026-09-07 | local cert | Docker restore / RQ / chaos drills | workstation | n/a (cert compose) | unassigned | See `ops/cert_*.json` — not a prod change |

Emergency changes use the same table plus an incident ID.
