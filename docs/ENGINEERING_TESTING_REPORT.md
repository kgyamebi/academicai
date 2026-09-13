# Testing / Coverage Report — AcademicCheck AI

Date: 2026-09-07  
CI (`.github/workflows/ci.yml`):

- Overall: `pytest --cov=app --cov-fail-under=70`
- Critical: billing + credits + deps `--cov-fail-under=75`
- Extra gates: AI quality, a11y static, reliability injection
- Frontend: `tsc --noEmit`, `npm run a11y`, Playwright a11y
- `pip-audit ... || true` (does **not** fail the job)

Do **not** raise `--cov-fail-under` to 90 until a green run exists.

## This pass

New file: `backend/tests/test_engineering_quality.py`

| Test | What it locks |
| --- | --- |
| `test_pdf_download_eager_loads_scores` | PDF/share score eager-load, `_owned_report`, no `db.get(AnalysisReport)` |
| `test_public_lists_are_capped` | blog 50 / FAQ 100 |
| `test_http_errors_are_structured` | 401 `{error,status}`, no traceback |
| `test_validation_errors_do_not_echo_internals` | 422 generic, no `loc` |
| `test_queue_helpers_log_unavailable_backends` | queue warning event names |
| `test_openapi_lists_core_contract_paths` | OpenAPI includes live/ready/login/assignments/reports/stripe webhook |

Isolation re-run this pass: `tests/test_isolation.py` included in the quality job, **passed**.

## Coverage (remeasure)

Command: `pytest -q --cov=app --cov-report=term`  
Result: **176 passed**, TOTAL **5657 statements, 1176 missed, 79%** (301.07 s).

Prior full run: 166 passed, 5598 stmts, 1165 missed, 79%. Extra engineering tests did **not** move TOTAL off 79%.

Target 90%: **FAIL**.

## Suite map (existing; not re-invented)

| Area | Tests |
| --- | --- |
| Unit / domain | analysis quality, credits, crypto, storage |
| Integration | API TestClient (SQLite) |
| Authorization | `test_isolation.py` |
| Billing | `test_billing_critical.py` |
| Documents | upload/security tests |
| Queue | `test_reliability_failures.py` (DLQ/cancel/reaper); live 1000-job drill is ops, not CI |
| Recovery | restore audit JSON, not pytest |
| Regression | CI job list above |
| E2E | Playwright a11y on 3100; not a full product E2E |

`app.workers.rq_worker` remains effectively untested in pytest (no fork/Redis worker in CI).

## Verdict

Critical-path HTTP isolation and billing ledger tests exist. Coverage gate in CI is 70/75, not 90. Testing score stays **79** until a new `--cov` TOTAL is pasted into this file.
