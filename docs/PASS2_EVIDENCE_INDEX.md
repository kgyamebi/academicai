# Pass 2 Evidence Index

Date: 2026-09-07  
Companion to `docs/CTO_PRODUCTION_GATES.md`, `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`, `docs/HUMAN_ACTION_LIST.md`.

## Pytest runs this pass

| Artifact | Content |
| --- | --- |
| `ops/cert_pass2_pytest.txt` | **25 passed** — `test_billing_critical`, `test_seo_sitemap`, `test_analysis_engine` |
| `ops/cert_pass2_meta.json` | Score deltas + file list |

## Code / config touched (Bucket A)

| Path | Why |
| --- | --- |
| `backend/app/services/billing.py` | Renewal extend on `invoice.paid`; payment lock; fail/refund/renewal counters; `_record_billing_analytics` |
| `backend/app/services/credits.py` | Expiry writes `CreditTransaction(status=expired)`; `wallet_matches_ledger` |
| `backend/app/api/v1/billing.py` | Checkout/credits rate limit; webhook duplicate counter; cancel analytics |
| `backend/app/core/rate_limit.py` | `checkout` bucket per plan |
| `backend/app/api/v1/citations.py` | `citation_check_used` analytics |
| `backend/app/services/analysis/runner.py` | Analysis-complete email (registered users) |
| `frontend/app/help/page.tsx` | FAQ section + `FAQPage` JSON-LD |
| `backend/tests/test_billing_critical.py` | Expiry ledger, renewal, analytics, checkout bucket |
| `backend/tests/test_analysis_engine.py` | Intro/conclusion/structure + weakest assertions |
| `backend/tests/test_seo_sitemap.py` | REQ-64 slug coverage vs `sitemap.ts` / `seed.py` |

## Prior artifacts still authoritative (unchanged this pass)

| Artifact | Gate relevance |
| --- | --- |
| `ops/cert_payment_keys.json` | Live PSP still **false** |
| `ops/cert_chaos_results.json` | `billing_provider_kill` **not_run** |
| `ops/cert_worker_death.json` | `pass: false` |
| `ops/cert_restore_audit.json` | Local restore only; managed PITR false |
| `ops/cert_http_results.json` / `ops/cert_k6_summary.json` | Scalability still below gate |
| `ops/grafana/*.json` | Spec only — not deployed |

## Bucket A not finished this pass (still open in-repo)

These remain PARTIAL and were **not** closed; do not treat as done:

- Full-suite coverage remeasure to ≥90%
- Automated mobile E2E / DOCX acceptance E2E
- Remaining missing emails (receipt, usage warning, renewal reminder)
- ClamAV-as-required (needs deploy — HAL-12)
- Editor depth / Improve Sentence population (product surface — not started)
- OpenAPI response typing completeness
