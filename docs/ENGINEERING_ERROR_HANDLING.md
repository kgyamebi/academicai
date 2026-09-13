# Error Handling Report — AcademicCheck AI

Date: 2026-09-07  
Companion: `docs/ENGINEERING_RELIABILITY_REPORT.md`.

## HTTP surface

`app/main.py`:

- `HTTPException` → `{error, status}` (no stack).
- `RequestValidationError` → 422 `"Please check the submitted information."` (no `loc`).
- Bare `Exception` → 500 `"Something went wrong. Please try again."` + `log.error("unhandled_error")`.
- CSRF failure in middleware returns the same JSON shape + `X-Request-ID`.

Pytest: `test_http_errors_are_structured`, `test_validation_errors_do_not_echo_internals`.

## User-visible vs internal

| Failure | User message | Logged? |
| --- | --- | --- |
| Unauthenticated | Please sign in / session expired | via status metrics 4xx |
| Not owned | 404 not found (no leak) | isolation tests |
| Rate limit | Please wait… / 503 if limiter down in prod | `rate_limit.py` |
| Queue down | 503 analysis workers unavailable | analysis router |
| Upload unreadable | Try PDF/DOCX/TXT/Markdown | documents router |
| Account storage delete | Account still deleted | `account_delete_storage_failed` (this pass) |

## Worker / IO

| Path | Before this pass | After |
| --- | --- | --- |
| `registered_workers` | `except: n=0` | warning `worker_count_unavailable` |
| `queue_depth` | `except: -1` | warning `queue_depth_unavailable` |
| `_job_already_terminal` | `except: False` | warning `terminal_job_lookup_failed` |
| `record_poison_job` DB fail | already `poison_job_mark_failed` | unchanged |

Returning `False` from `_job_already_terminal` on DB errors can still allow a re-enqueue attempt; Redis/RQ then fail closed. That residual is logged, not eliminated.

## Remaining

- Extractor `except Exception` mapped to user 400 in several branches — correct for untrusted files; still broad.
- Sentry init failure is logged; DSN unset here so Sentry is unused.
- Frontend: fetch abort timeouts exist; no new error-boundary audit with screenshots this pass.

## Verdict

API errors are structured and non-leaking in pytest. Silent queue/account-delete paths were reduced. This is **not** a claim of zero unhandled exceptions in all adapters.
