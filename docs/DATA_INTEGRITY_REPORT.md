# Data Integrity Report — AcademicCheck AI

Date: 2026-09-07  
Financial ledger detail: `docs/FINANCIAL_INTEGRITY_REPORT.md`.

| Entity | Partial write | Duplicate | Orphan | Evidence |
| --- | --- | --- | --- | --- |
| Assignments | Session rollback | User-scoped PK | Cascade with user | Isolation + restore fingerprints |
| Documents | Store-then-commit; `delete_bytes` on rollback | UUID storage key | Compensating delete | Code path; no fault-injected S3 |
| Analysis jobs | Status machine; reap stale | RQ `job_id` | Reaper fails + refund | pytest reap / poison / cancel |
| Reports | Unique `job_id`; persist guard | IntegrityError → existing row | — | Prior reliability tests |
| Findings | Loaded with report persist | — | Drop-table restore recovered | Restore after_drop_findings |
| Payments | Record-before-apply; unmatched webhook not processed | Idempotency key reuse on failed | — | billing pytest |
| Subscriptions | Second sub cancels first | — | — | billing pytest |
| Credits | reserve / consume / refund | Reservation per job | Stale job refund | pytest wallet 5→5 |
| Billing transactions | Ledger rows with payment | Webhook replay no double-grant | — | `test_billing_critical.py` |

Restore drill fingerprints matched for users, assignments, documents, reports, jobs, findings, payments, credits, subscriptions (`ops/cert_restore_audit.json`).

Live PSP double-charge: **not tested** (keys absent).

## Verdict

In-repo integrity controls for assignments, documents, reports, jobs, and ledger are **pytest-backed**. Orphan S3 objects and live duplicate charges are **not certified**.
