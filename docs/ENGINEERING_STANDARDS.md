# Engineering Standards Guide — AcademicCheck AI

Date: 2026-09-07  
These standards describe **existing** practice. They do not add product features.

## Code structure

1. HTTP in `api/v1`; business rules in `services`; ORM in `models`; jobs in `workers`.
2. Do not import API routers from workers or services.
3. Ownership: filter `user_id` in SQL or use `deps.owned_*`. Never trust a client id alone.
4. Do not `selectinload` unbounded child collections (findings). Page them.
5. Public list queries must have a SQL `LIMIT`.
6. Do not swallow `Exception` on IO without a structured log event.

## Naming

| Kind | Pattern |
| --- | --- |
| Log/metric events | `snake_case` verb or object_result |
| SQL indexes | `ix_<table>_<cols>` |
| Tests | `test_<behavior>` |
| Alembic | monotonic `00N_` |

## Testing

- Every IDOR-sensitive route needs an isolation case.
- Source-assert tests are allowed for query/load patterns that are hard to see in SQLite.
- Coverage floors: 70 overall, 75 billing+credits+deps. Do not raise CI to 90 until a measured run is green.
- Do not mock live PSPs, Grafana, or PITR as if they ran.

## Documentation

- Put proof in `ops/*.json` or pytest output.
- If a drill did not run, write **not run** / **FAIL**.

## Migrations

- Prefer idempotent index creates.
- Production: Alembic only. `create_all` is development/test.

## Monitoring

- Ready vs live as above.
- Alerts: `docs/ALERT_CATALOG.md`. Wire them on the host; do not claim they fire in production from this repo alone.
