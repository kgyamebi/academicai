# Maintainability Report — AcademicCheck AI

Date: 2026-09-07  
Companions: `docs/ENGINEERING_STANDARDS.md`, `docs/DEVELOPER_PLAYBOOK.md`, `docs/OPERATIONAL_PLAYBOOK.md`.

## Structure (enforced by current layout)

```
backend/app/api/v1     HTTP
backend/app/services   domain
backend/app/models     ORM
backend/app/workers    RQ
backend/alembic        migrations
frontend/app            routes
frontend/components     shared UI
ops/                    measured cert JSON
docs/                   evidence reports
```

## Naming

- Routers: resource plural prefixes (`/api/assignments`).
- Tests: `test_<area>_*.py`.
- Metrics/logs: snake_case event names (`account_delete_storage_failed`).
- Alembic: `00N_description.py` with integer revision ids.

## Testing standard (as enforced)

- Isolation tests for every owned resource.
- CI `--cov-fail-under=70` overall, `75` billing/credits/deps.
- Do not raise to 90 until green.
- Isolation 100 is **repository suite only**.

## Documentation standard

- Gate claims require `ops/cert_*.json` or pytest names.
- Unrun drills are **FAIL**, not “likely pass.”

## Migrations standard

- Additive indexes via `_ensure_index` (idempotent).
- No `create_all` in staging/production lifespan.
- Head is **007**.

## Monitoring standard

- Scrape `/api/metrics/prometheus` per replica.
- `/api/ready` is the dependency probe; `/api/live` is process-up only.
- Process counters reset on restart.

## This-pass maintainability work

- `_owned_report` removes four-copy ownership fetch.
- Public query caps documented in tests so they cannot regress unbounded.
- Queue failures emit named log events for grep/alerts.

## Remaining

- `engine.py` size (TD-01).
- Untyped API dicts (TD-05).
- Dual SQLite CI vs Postgres prod (TD-09).

## Verdict

Conventions are consistent enough to extend safely. Maintainability is **not** a launch gate pass.
