# AcademicCheck AI

**Check, improve, and understand your academic work before submission.**

AcademicCheck AI is a global academic writing analysis platform. It checks an assignment against its question, structure, argument, evidence, academic writing quality and citations, then gives actionable feedback.

It is **not** an essay generator, a guaranteed grader, a plagiarism verdict engine, or a definitive AI detector.

## Product overview

Students paste or upload a draft, add the assignment question, choose academic level and citation style, and receive a diagnostic report:

- Did I answer the question?
- Is the thesis clear and arguable?
- Are claims supported?
- Is the structure logical?
- Are citations consistent with the reference list?
- What should I fix first?

Scores are **AI-assisted diagnostic indicators, not official grades**.

Academic integrity rules:

- Does not write an entire assignment for submission
- Does not invent sources, quotations, statistics, or page numbers
- Does not claim a guaranteed mark
- Treats uploaded documents as untrusted data (prompt-injection resistant)
- Does not use student work for model training unless the user opts in

## Architecture

```
Frontend (Next.js)  →  FastAPI  →  PostgreSQL
                         ↓
                   Redis + RQ worker
                         ↓
              Heuristic analysis + optional LLM
                         ↓
                    Object storage
```

Business logic does not depend on a single AI or payment provider.

```
AcademicCheck AI
        ↓
Shared global payment layer
        ↓
Provider adapters (Stripe / Paystack / Flutterwave)
```

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, TypeScript, React, Tailwind CSS, TipTap |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| Queue | Redis + RQ |
| Documents | PyMuPDF, python-docx, ReportLab |
| Storage | Local disk (default) or S3/R2-compatible |
| Auth | Email/password, verification, reset, guest sessions |

## Installation

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000
- OpenAPI: http://localhost:8000/api/docs

### Local backend (without full Docker)

Start PostgreSQL and Redis, then:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
set DATABASE_URL=postgresql+psycopg://academiccheck:academiccheck@localhost:5432/academiccheck
uvicorn app.main:app --reload --port 8000
```

Worker (optional; the API falls back to in-process analysis if Redis is down):

```bash
python -m app.workers.rq_worker
```

### Local frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

See `.env.example`. Important groups:

- `APP_SECRET_KEY`, `JWT_SECRET_KEY`
- `DATABASE_URL`, `REDIS_URL`
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` (optional)
- `STRIPE_*`, `PAYSTACK_*`, `FLUTTERWAVE_*`
- `STORAGE_BACKEND`, `S3_*`
- `EMAIL_PROVIDER`, `SMTP_*`
- Guest retention: `GUEST_RETENTION_HOURS`

Heuristic analysis works **without** an AI key. When a key is present, the system may enrich the summary and coach replies. Model output is schema-validated and never shown raw.

## Database setup and migrations

Tables are created on API startup in development. For production:

```bash
cd backend
alembic upgrade head
```

Seed data (plans, SEO pages, FAQs, default admin) runs once when roles are missing.

Default admin (change immediately):

- Email: `admin@academiccheck.ai`
- Password: `ChangeMeAdmin123!`

## AI provider setup

Set one or more keys. Routing:

- Fast/cheap models: classification-style tasks
- Stronger models: synthesis and coach
- Fallback order: default provider → OpenAI → Anthropic → Gemini
- If all fail, heuristic results are returned. The API does not silently invent a report.

Prompt version is stored on each analysis job (`v1.0.0`).

## Storage setup

Default: `STORAGE_BACKEND=local` and `STORAGE_LOCAL_PATH`.

S3/R2: set endpoint, keys, bucket. Signed-URL delivery can be added without changing ownership rules.

## Payment setup

Plans and prices live in the `plans` table and can be changed in `/api/admin/plans`.

Checkout creates a `pending` payment. **Accounts upgrade only after a signed webhook**. The frontend cannot declare a successful payment.

Idempotency is enforced on provider event IDs.

## Email setup

`EMAIL_PROVIDER=console` prints mail in development (verification and reset links). Set `smtp` for production.

## Redis setup

Used for background analysis. If Redis is unavailable, the API processes the job inline so local development still works.

## Development commands

```bash
# API
uvicorn app.main:app --reload --port 8000

# Worker
python -m app.workers.rq_worker

# Tests
cd backend && pytest

# Frontend
cd frontend && npm run dev
```

## Testing

```bash
cd backend
pytest -q
```

Coverage includes question interpretation, analysis scoring, file-signature rejection, guest analysis, and tenant isolation (another user cannot read an assignment by ID).

## Production deployment

Provider-agnostic:

1. Build `backend` and `frontend` images (or deploy frontend to Vercel and API to Railway/Render/Fly/AWS).
2. Provision PostgreSQL, Redis, and object storage.
3. Set production secrets; disable `APP_DEBUG`.
4. Run `alembic upgrade head`.
5. Put TLS in front of the API and web app.
6. Point `APP_WEB_URL`, `APP_API_URL`, and CORS origins at the real hosts.

Health check: `GET /api/health`.

## Security

- Password hashing (bcrypt)
- Signed JWTs; guest tokens expire with guest retention
- Tenant isolation: every assignment/document/report is loaded by authenticated user id, never by trusting a client-supplied owner
- Upload limits, MIME + signature checks, zip-bomb and path-traversal guards
- Rate limits by plan on login, signup, upload, analysis, and coach
- CSRF-relevant cookie use is avoided for API auth (Bearer tokens)
- Structured logs; no stack traces or secrets in client errors
- Documents treated as untrusted; assignment text cannot override system instructions

## Data retention

- Guest uploads: short retention (default 24 hours)
- Account documents: until the user deletes them or a policy applies
- Account deletion: disables login, clears document text and files
- Financial records may be retained where the law requires it

## AI limitations

- Feedback can be wrong or incomplete
- Relevance and rubric scores are interpretations of wording, not a lecturer’s judgement
- Citation verification may miss legitimate sources
- AI-writing indicators are uncertain stylistic signals
- Always follow institutional academic-integrity policy

## Phase 1 (this repository)

Landing, guest checker, authentication, assignment workspace, paste/DOCX/PDF upload, question analyzer, relevance, thesis, structure, argument, evidence, grammar, academic writing, citation/reference checks, report, PDF export, dashboard, configurable billing, SEO/help pages, admin basics, tests.

## Later phases

Rubric verification integrations, richer Crossref/OpenAlex matching, institution SSO, LMS, licensed plagiarism providers, and research-workflow tools — without turning the product into an assignment generator.
