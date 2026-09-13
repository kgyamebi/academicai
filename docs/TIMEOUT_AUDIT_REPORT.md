# Timeout Audit Report — AcademicCheck AI

Date: 2026-09-07  
Rule: no infinite wait on external I/O. Evidence is source plus pytest source assertions in `tests/test_reliability_hardening.py`.

| Operation | Timeout | On expiry | Evidence |
| --- | --- | --- | --- |
| Postgres connect | 3 s | Ready 503 | `session.py` connect_args; prior chaos hung without this |
| Postgres statement | 30 s | Query abort | `options: statement_timeout=30000` this pass |
| Postgres lock wait | 10 s | Lock abort | `lock_timeout=10000` this pass |
| Postgres pool checkout | 30 s | Request fail | `pool_timeout=30` (prior) |
| Redis sockets (shared pool) | 2 s connect / 2 s | Fail-closed enqueue; prod rate-limit 503 | `queue.py`; rate_limit now reuses pool |
| RQ job | 600 s | Job failure + DLQ path | `queue.py` job_timeout |
| S3 connect / read | 5 s / 15 s | StorageError; circuit failure | `storage.py` botocore Config this pass |
| AI HTTP | `ai_timeout_seconds` 90 | Next provider / heuristic | `provider.py` httpx |
| OpenAlex / Crossref / S2 | 4 s | Skip source verify | `verify_sources.py` |
| Paystack / Flutterwave HTTP | 15 s | 502 + circuit failure | `billing.py` this pass |
| Stripe HTTP client | 15 s (was library default 80 s) | 502 + circuit failure | `new_default_http_client(timeout=15)` this pass |
| SMTP | 15 s | Logged; register continues | `emailer.py` this pass |
| ClamAV | 8 s | Scan skipped/fail per caller | `validation.py` |
| Frontend API | 60 s (180 s uploads) | User-visible timeout error | `frontend/lib/api.ts` this pass |
| Webhook handler | Starlette/uvicorn default | 503 if payment missing (retryable) | No infinite app-level wait; provider retry is their job |

## Gaps (not claimed closed)

- Uvicorn keep-alive / proxy idle timeouts are **host config**, not in this repo’s runtime.
- PDF generation on the API has **no separate deadline** (workflow freeze: not moved to workers).
- Network partition drill **not run**.

## Verdict

In-process external calls have finite timeouts and graceful failure paths. **Not** a 98 timeout certificate without host proxy and partition drills.
