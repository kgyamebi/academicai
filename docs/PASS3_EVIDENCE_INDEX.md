# Pass 3 Evidence Index

Date: 2026-09-07  
Companion: `docs/CTO_PRODUCTION_GATES.md`, `docs/HUMAN_ACTION_LIST.md`, `ops/cert_pass3_meta.json`.

## Measured runs

| Artifact | Result |
| --- | --- |
| `ops/cert_pass3_pytest.txt` | Pass3 hardening suite green |
| `ops/cert_pass3_coverage.txt` | **208 passed**, TOTAL coverage **80.98%** (5820 stmts, 1107 missed) |

## Code / config

| Path | Category |
| --- | --- |
| `backend/app/core/csrf.py` | Security — `csrf.rejected` metric + log |
| `backend/app/services/billing.py` | Security/Billing — `billing.webhook_signature_invalid` |
| `backend/app/api/v1/billing.py` | Billing — Paystack/Flutterwave UUID lookup fix |
| `backend/app/services/analysis/runner.py` | Reliability/Obs — `jobs.started` / `jobs.completed` |
| `backend/app/workers/queue.py` | Reliability — `jobs.dead_letter` |
| `backend/alembic/versions/008_payments_security_indexes.py` | Scalability |
| `docker-compose.prod.yml` | Scalability — `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` under PgBouncer |
| `ops/prometheus/alert-rules.yml` | Observability — A-PAY on `billing.failed_payments` |
| `ops/rollback_compose.sh` | Operations/Deployment |
| `frontend/app/app/settings/page.tsx` | Accessibility — alertdialog Tab focus trap |
| `backend/tests/test_pass3_hardening.py` | All — assertions |

## Explicitly not claimed

Live PSP charges, hosted Grafana scrape, managed PITR, pentest, on-call staffing, coverage ≥90%.
