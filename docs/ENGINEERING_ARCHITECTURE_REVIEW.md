# Architecture Review — AcademicCheck AI

Date: 2026-09-07  
Scope: repository audit only. No product redesign. No score inflation.

## Layering (as implemented)

| Layer | Location | Responsibility |
| --- | --- | --- |
| HTTP | `backend/app/api/v1/*` | Auth, ownership, pagination, serialization |
| Domain services | `backend/app/services/*` | Auth, billing, credits, analysis, storage |
| Workers | `backend/app/workers/*` | RQ enqueue, retries, DLQ, job execution |
| Persistence | `backend/app/models/*`, `app/db/session.py` | SQLAlchemy models, pool, timeouts |
| Frontend | `frontend/app/*`, `frontend/components/*` | Next.js App Router pages |

Request path: FastAPI router → `deps` (auth/ownership) → service or query → SQLAlchemy session. Analysis work is intended to leave the API process via RQ (`enqueue_analysis` + `run_analysis_job`).

## SOLID / SoC findings

| Principle | Status | Evidence |
| --- | --- | --- |
| Single responsibility | Partial | Routers are thin; `engine.py` still owns all heuristic analyzers in one module |
| Dependency inversion | Partial | Services import FastAPI `HTTPException` (`auth.py`, `billing.py`, `credits.py`, `entitlements.py`) |
| Open/closed | Partial | Provider adapters exist; heuristic engine is a closed function graph |
| Interface segregation | Pass for HTTP | `deps.owned_assignment` / `owned_document` keep IDOR checks out of each handler |
| Least knowledge | Partial | Report handlers previously duplicated ownership queries; now `_owned_report` |

## Cyclic dependencies

No Python import cycle was found on the API → service → model path. Workers import `app.services.analysis.runner` and `app.db.session`; they do not import API routers.

Hidden coupling (not a cycle, still a violation):

- Domain services raise FastAPI `HTTPException`, so they cannot be reused outside Starlette without that stack.
- `get_db` rolls back on `HTTPException`; auth refresh must `db.commit()` before 401 (`app/services/auth.py`). That coupling is load-bearing.

## Large units (not split this pass)

| Unit | Why it stays | Risk of split |
| --- | --- | --- |
| `app/services/analysis/engine.py` (`run_analysis` and category helpers) | F1 gates are tied to this module | Split without gold re-run can drop CI F1 |
| `frontend/app/check/page.tsx` | Single check workflow; assignment route re-exports it | UX freeze |
| `frontend/app/app/assignments/[id]/report/page.tsx` | Report rendering | a11y lab already covers this route |

This pass did **not** decompose those files.

## This-pass structural fixes (code)

| Change | Location | Why |
| --- | --- | --- |
| `_owned_report` | `app/api/v1/reports.py` | One ownership query; `user_id` in SQL `WHERE` |
| Share eager-load scores | `_shared_report` | Avoid lazy `report.scores` on public share |
| Public list caps | `app/api/v1/public.py` | `.limit(50)` blog, `.limit(100)` FAQs |
| Queue failure logs | `app/workers/queue.py` | Worker count / depth / terminal lookup no longer silent |

Verification: `tests/test_engineering_quality.py`, `tests/test_scale_hardening.py`, `tests/test_isolation.py`.

## Remaining architectural debt

1. Service-layer HTTP exceptions (FastAPI leak).
2. PDF built on the API request thread (`download_pdf` → `build_pdf_report`).
3. In-process metrics (`app/core/metrics.py`) are not a shared telemetry backend.
4. Most routes return untyped `dict` (OpenAPI incomplete except auth `TokenResponse`).

## Verdict

Layering is coherent for a monolith API + worker. It is **not** a certified hexagonal/clean-architecture rewrite. Remaining violations are documented, not estimated away.
