# Developer Playbook — AcademicCheck AI

Date: 2026-09-07

## Layout

- API: `backend/` (FastAPI). Tests: `backend/tests/`.
- Web: `frontend/` (Next.js 15). A11y: `frontend/a11y/`.
- Evidence: `ops/cert_*.json`, `docs/ENGINEERING_*.md`.

## Local API tests

From `backend/`, Python 3.12+ (CI) or 3.14 locally:

```
py -3.14 -m pytest -q
py -3.14 -m pytest -q --cov=app --cov-fail-under=70
```

Critical packages:

```
py -3.14 -m pytest -q tests/test_isolation.py tests/test_billing_critical.py tests/test_hardening.py tests/test_security_cert.py --cov=app.services.billing --cov=app.services.credits --cov=app.deps --cov-fail-under=75
```

JWT in test env must be ≥ 32 bytes (`ci-jwt-secret-key-32-bytes-minimum` in CI).

PowerShell: do not chain with `&&`. Use `;` or separate commands.

## Frontend

```
cd frontend
npm ci
npx tsc --noEmit
npm run a11y
```

Playwright a11y expects the helper API on port **3100**.

## Schema

- Dev/test: `create_all` on startup when `APP_ENV` is development/test.
- Staging/production: Alembic. Head revision **007**.
- Do not point production at SQLite (`lifespan` raises).

## Queue

Workers: `python -m app.workers.rq_worker` with Redis. Analysis enqueue no-ops/fails closed without registered workers.

## What not to do

- Do not add product features in hardening work.
- Do not inflate scores or mark launch approved.
- Do not commit `.env`.
- Do not treat repo isolation 100 as a live-host certificate.
