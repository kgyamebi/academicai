# Attack Surface Report — AcademicCheck AI

Date: 2026-09-07  
Companion: `docs/THREAT_MODEL.md`. Frontend never authorizes.

| Surface | Entry | Trust | Authn | Authz evidence |
| --- | --- | --- | --- | --- |
| Marketing / public API | `/`, `/api/public/*` | Unauthenticated | None | Caps `.limit(50/100)` |
| Auth | `/api/auth/*` | Cookies + Bearer | Argon2id / guest JWT | Rate limit login/signup |
| Tenant API | assignments, documents, analysis, reports, PDF, coach, citations, dashboard | JWT | Ownership 404 | isolation pytest |
| Billing | checkout, credits, payments, cancel, webhooks | JWT + HMAC webhooks | user_id on rows | billing isolation pytest |
| Admin | `/api/admin/*` | `require_roles("admin")` | Role | guest/student 403 pytest |
| Uploads | `/api/documents/upload` | JWT | user_id path | document_security pytest |
| AI | enhance/coach HTTP | JWT + untrusted wrap | assignment ownership | prompt_injection pytest |
| Storage | local / S3 | keys | traversal reject | storage tests |
| Webhooks | `/api/billing/webhooks/*` | HMAC | event_id replay table | billing_critical pytest |
| Workers | Redis RQ | internal | job_id in DB | fail-closed enqueue |
| CI | GitHub Actions | GitHub | — | pip-audit non-blocking |

Unmeasured: TLS terminator, WAF, DAST, host pentest.
