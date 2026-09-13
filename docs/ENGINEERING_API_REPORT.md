# API Hardening Report — AcademicCheck AI

Date: 2026-09-07  
Routers: auth, assignments, documents, analysis, reports, coach, billing, dashboard, public, admin, health.

## Contract

- Structured errors: `{ "error": string, "status": int }` (`app/main.py` handlers).
- Validation: 422 does **not** echo `loc` (`test_validation_errors_do_not_echo_internals`).
- Unhandled: 500 generic message; `unhandled_error` log (`test_http_errors_are_structured` on 401).
- OpenAPI: generated at `/api/openapi.json` in development/test; disabled in production; staging is admin-gated.
- Core paths present: `test_openapi_lists_core_contract_paths`.
- Typed `response_model`: auth token routes only. Remaining endpoints are implicit dicts — OpenAPI is **incomplete**, not inaccurate for those paths.

## Per-concern audit

| Concern | Status | Evidence |
| --- | --- | --- |
| Validation | Pydantic on write bodies; Query ge/le on pages | `AssignmentCreateIn`, report `page_size` ≤ 100, assignment ≤ 50 |
| Authorization | `get_current_user`; ownership `user_id` in WHERE or `owned_*` | `tests/test_isolation.py` |
| Admin | `require_roles("admin")` | isolation + admin tests |
| Idempotency | Analysis `job_id` + `DuplicateJobError`; billing webhook event ids | queue + `test_billing_critical.py` |
| Pagination | Assignments, reports findings, admin lists | public blog/FAQ capped this pass, same `{items}` shape |
| CSRF | Middleware `enforce_csrf` | hardening tests |
| Rate limit | Redis; production fail-closed 503 | `rate_limit.py`; login test uses staging to avoid that trap |
| Oversized payloads | Upload MB cap; analytics properties stripped of `text`/`document`/`assignment`/`content` and truncated | `documents.py`, `public.py` |
| Duplicate queries | Report GET no longer dumps all findings; PDF/share use shared ownership helper | `reports.py`, scale tests |

## Endpoint notes (no new routes)

- `GET /api/live` — liveness, no deps.
- `GET /api/ready` — 503 when DB/Redis fail (chaos 2026-09-07T12:36:39Z).
- `GET /api/reports/{id}/pdf` — ownership filter + scores eager-load; PDF still CPU on the request.
- Webhooks — HMAC + replay table; **live keys absent** (`ops/cert_payment_keys.json`).

## Eliminated this pass

- Unbounded public blog/FAQ selects.
- PDF `db.get` without `user_id` in the query (IDOR already required a match; SQL now encodes it).
- Share/revoke `db.get` then Python ownership check — now `_owned_report`.

## Remaining

- Untyped OpenAPI for non-auth routes.
- Share GET still returns up to 80 findings with no `page` query (existing contract).
- PDF payload size unbounded by finding count inside `build_pdf_report`.
- No HTTP idempotency-key on checkout POST beyond provider/session semantics already in billing.

## Verdict

API error shape and ownership filters are pytest-backed. OpenAPI is **not** a full contract. Live billing webhooks are **not** certified.
