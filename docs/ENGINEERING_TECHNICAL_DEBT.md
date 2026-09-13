# Technical Debt Report — AcademicCheck AI

Date: 2026-09-07  
Rule: only items with a file, test, or measured artifact. No estimated “% improvement.”

## Resolved this pass (evidence)

| Item | Location | Fix | Verification |
| --- | --- | --- | --- |
| PDF loaded report without scores / used `db.get` | `app/api/v1/reports.py` `download_pdf` | `_owned_report` + `selectinload(AnalysisReport.scores)` | `test_pdf_download_eager_loads_scores` |
| Share serialize could lazy-load scores | `_shared_report` | `selectinload(AnalysisReport.scores)` | same test reads `_shared_report` |
| Duplicate ownership `db.get` on share/revoke | `create_share`, `revoke_share` | `_owned_report` | source assert + isolation 404 |
| Unbounded public blog/FAQ queries | `app/api/v1/public.py` | `.limit(50)` / `.limit(100)` | `test_public_lists_are_capped` |
| Account delete swallowed storage errors | `app/api/v1/auth.py` | `log.error("account_delete_storage_failed")` | source in `delete_account` |
| Queue helpers swallowed exceptions | `app/workers/queue.py` | structured warnings | `test_queue_helpers_log_unavailable_backends` |
| Duplicate Playwright `env:` in CI | `.github/workflows/ci.yml` | single `env` block | file review |

## Open debt (intentionally not “fixed” by rewrite)

| ID | Location | Smell | Impact | Why not rewritten | Remaining risk |
| --- | --- | --- | --- | --- | --- |
| TD-01 | `services/analysis/engine.py` | Large module, many helpers | Harder reviews | AI F1 CI is coupled to this file | Regressions if split without gold re-run |
| TD-02 | `services/auth.py`, `billing.py`, `credits.py` | HTTPException in domain | Framework leak | Would be a wide API-shape change | Services unusable off FastAPI |
| TD-03 | `api/v1/reports.py` `download_pdf` | Sync PDF on request | Blocks a worker for PDF CPU | Moving PDF to RQ changes UX/timeouts | Latency spikes under concurrent PDF |
| TD-04 | Assignment/report lists | OFFSET pagination | Deep pages degrade | Cursor tokens would change list JSON | Slow deep pages at high volume |
| TD-05 | Most routers | No `response_model` | OpenAPI drift | Adding models can change JSON | Clients rely on implicit dicts |
| TD-06 | `core/metrics.py` | Process-local counters | Lost on restart; per replica | Grafana/OTel not in this environment | Dashboards cannot be claimed |
| TD-07 | `workers/rq_worker.py` | 0% line coverage historically | Worker entry untested in pytest | Needs live Redis in CI | SIGTERM path unexercised in CI |
| TD-08 | Alembic vs `create_all` | Dual schema paths | Drift if someone runs prod with `create_all` | Prod lifespan skips `create_all` | Mis-set `APP_ENV` |
| TD-09 | SQLite in CI | Not Postgres | Dialect drift | Cert DB is Docker Postgres 55432 | Index/SQL differences |
| TD-10 | Frontend check + report pages | Large client components | Bundle/maintainability | Product freeze | Incremental a11y/perf work only |

## Dead code

No `TODO` / `FIXME` / `NotImplemented` markers in application Python/TS. Unused product surfaces were not deleted (would be a product change). `cert_ping` in `workers/tasks.py` is ops-only, documented as such.

## Duplicate code remaining

- Category scoring helpers in `engine.py` share clamp/score patterns — left in place.
- Billing provider checkout blocks (Stripe/Paystack/Flutterwave) are similar by design (three PSPs).

## Inconsistent patterns

| Pattern | Canonical | Exceptions |
| --- | --- | --- |
| Ownership | `deps.owned_*` or SQL `user_id == user.id` | Admin routes use role gate |
| Errors | `{error, status}` via handlers | FastAPI default unused |
| Pagination | `page` + `page_size` + `total` | Public blog/FAQ return `{items}` only (capped, shape unchanged) |
| Auth contract | `TokenResponse` | Other routes untyped |

## Verdict

Debt is catalogued. This pass removed silent failures and query duplication on reports/public/queue. It did **not** pay TD-01–TD-10. Those remain open.
