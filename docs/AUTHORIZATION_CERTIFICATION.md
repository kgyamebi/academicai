# Authorization Certification — AcademicCheck AI

Date: 2026-09-09  

## Zero-trust enforcement

- Never trust path/body/query IDs — `owned_*` / `_owned_report` / `user_id == current`.
- Never trust frontend ownership — server ORM filters only.
- Default deny — missing row → **404** (no 403 oracle).
- Admin — `require_roles` + MFA enabled for privileged.
- Least privilege — student cannot admin (pytest).

## Endpoint matrix (pytest)

| Resource | Result |
| --- | --- |
| Assignments, documents, analysis, reports, PDF | IDOR → 404 |
| Coach, citations, versions compare | denied |
| Payments, subscription cancel, credits view | isolated |
| Admin overview | student/guest → 403; MFA required for admin role |

**Certification: PASS (pytest).** **FAIL (host)** until independent pentest (HAL-07).
